"""
Production AI Response Generation with persona management and knowledge base RAG
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import structlog
from openai import AsyncOpenAI
import tiktoken

from app.config import settings
from app.database import get_db_pool
from app.vector_store import search_similar_documents
from app.prompt_builder import PromptBuilder
from app.content_moderator import ContentModerator
from app.quality_scorer import QualityScorer
from app.message_queue import publish_message
from app.metrics import (
    responses_generated,
    generation_time,
    token_usage,
    generation_errors,
)

logger = structlog.get_logger()


class ResponseGenerator:
    """Production-grade AI response generation engine"""

    def __init__(self):
        self.perplexity_client: Optional[AsyncOpenAI] = None
        self.gemini_client: Optional[AsyncOpenAI] = None
        self.prompt_builder = PromptBuilder()
        self.content_moderator = ContentModerator()
        self.quality_scorer = QualityScorer()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def initialize(self):
        """Initialize LLM clients"""
        # Initialize Perplexity client
        self.perplexity_client = AsyncOpenAI(
            api_key=settings.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
        
        # Initialize Gemini client (OpenAI compatible)
        self.gemini_client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        logger.info("AI clients initialized (Perplexity & Gemini)")

    async def process_detected_post(self, message: Dict):
        """Process a detected post and generate response"""
        start_time = datetime.now()

        post_id = message["post_id"]
        organization_id = message["organization_id"]
        platform = message["platform"]
        persona_id = message.get("persona_id")
        auto_reply = message.get("auto_reply", False)

        logger.info(
            "Processing detected post",
            post_id=post_id,
            organization_id=organization_id,
            platform=platform,
        )

        try:
            # Fetch post details
            post = await self.fetch_post(post_id)
            if not post:
                logger.error("Post not found", post_id=post_id)
                return

            # Fetch persona
            persona = await self.fetch_persona(persona_id) if persona_id else None
            if not persona:
                persona = await self.get_default_persona(organization_id)

            # Retrieve relevant knowledge
            knowledge_docs = await self.retrieve_knowledge(
                post["content"], persona["knowledge_base_ids"]
            )

            # Build prompt
            prompt = self.prompt_builder.build_response_prompt(
                post=post,
                persona=persona,
                knowledge=knowledge_docs,
                platform=platform,
            )

            # Generate response
            response_text, metadata = await self.generate_with_llm(
                prompt=prompt,
                persona=persona,
                organization_id=organization_id,
            )

            # Moderate content
            is_safe, safety_score = await self.content_moderator.check(response_text)
            if not is_safe:
                logger.warning(
                    "Generated response failed content moderation",
                    post_id=post_id,
                    safety_score=safety_score,
                )
                response_text = await self.regenerate_safe_response(prompt, persona)

            # Score quality
            quality_score = await self.quality_scorer.score(
                response=response_text,
                post=post,
                persona=persona,
            )

            # Save response
            response_id = await self.save_response(
                post_id=post_id,
                persona_id=persona_id,
                response_text=response_text,
                metadata=metadata,
                quality_score=quality_score,
                safety_score=safety_score,
                auto_approved=auto_reply and quality_score >= 0.8,
            )

            # Track cost
            await self.track_cost(organization_id, metadata)

            # Publish event
            await publish_message(
                "response.generated",
                {
                    "response_id": str(response_id),
                    "post_id": str(post_id),
                    "organization_id": str(organization_id),
                    "quality_score": quality_score,
                    "auto_approved": auto_reply and quality_score >= 0.8,
                },
            )

            generation_duration = (datetime.now() - start_time).total_seconds()
            generation_time.labels(
                provider=metadata["provider"], model=metadata["model"]
            ).observe(generation_duration)

            responses_generated.labels(
                platform=platform, provider=metadata["provider"]
            ).inc()

            logger.info(
                "Response generated",
                response_id=response_id,
                quality_score=quality_score,
                duration=generation_duration,
            )

        except Exception as e:
            logger.error(
                "Error generating response", post_id=post_id, error=str(e), exc_info=True
            )
            generation_errors.labels(provider="unknown", error_type=type(e).__name__).inc()

    async def fetch_post(self, post_id: str) -> Optional[Dict]:
        """Fetch post from database"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, organization_id, platform, external_id, url, parent_url,
                       title, content, author, subreddit, engagement_score,
                       relevance_score, keyword_matches, metadata
                FROM detected_posts
                WHERE id = $1
                """,
                post_id,
            )

            if row:
                return dict(row)
        return None

    async def fetch_persona(self, persona_id: str) -> Optional[Dict]:
        """Fetch persona from database"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT p.id, p.name, p.voice_profile, p.system_prompt,
                       p.example_responses, p.temperature, p.max_tokens,
                       ARRAY_AGG(pkb.knowledge_base_id) as knowledge_base_ids
                FROM personas p
                LEFT JOIN persona_knowledge_bases pkb ON p.id = pkb.persona_id
                WHERE p.id = $1 AND p.active = true
                GROUP BY p.id
                """,
                persona_id,
            )

            if row:
                return dict(row)
        return None

    async def get_default_persona(self, organization_id: str) -> Dict:
        """Get default persona for organization"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT p.id, p.name, p.voice_profile, p.system_prompt,
                       p.example_responses, p.temperature, p.max_tokens,
                       ARRAY_AGG(pkb.knowledge_base_id) as knowledge_base_ids
                FROM personas p
                LEFT JOIN persona_knowledge_bases pkb ON p.id = pkb.persona_id
                WHERE p.organization_id = $1 AND p.active = true
                GROUP BY p.id
                ORDER BY p.created_at ASC
                LIMIT 1
                """,
                organization_id,
            )

            if row:
                return dict(row)

        # Fallback default
        return {
            "id": None,
            "name": "Default",
            "voice_profile": {"tone": "professional", "style": "helpful"},
            "system_prompt": "You are a helpful assistant.",
            "temperature": 0.7,
            "max_tokens": 500,
            "knowledge_base_ids": [],
        }

    async def retrieve_knowledge(
        self, query: str, knowledge_base_ids: List[str], top_k: int = 5
    ) -> List[Dict]:
        """Retrieve relevant knowledge from vector store"""
        if not knowledge_base_ids:
            return []

        try:
            results = await search_similar_documents(
                query=query, knowledge_base_ids=knowledge_base_ids, top_k=top_k
            )
            return results
        except Exception as e:
            logger.error("Error retrieving knowledge", error=str(e))
            return []

    async def generate_with_llm(
        self, prompt: str, persona: Dict, organization_id: str
    ) -> tuple[str, Dict]:
        """Generate response using LLM with fallback"""
        temperature = persona.get("temperature", 0.7)
        max_tokens = persona.get("max_tokens", 500)

        # Try Perplexity first
        try:
            response = await self.perplexity_client.chat.completions.create(
                model=settings.PERPLEXITY_MODEL,
                messages=[
                    {"role": "system", "content": persona.get("system_prompt", "")},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                presence_penalty=0.6,
                frequency_penalty=0.3,
            )

            content = response.choices[0].message.content
            metadata = {
                "provider": "perplexity",
                "model": settings.PERPLEXITY_MODEL,
                "tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "cost": self.calculate_perplexity_cost(response.usage),
            }

            token_usage.labels(provider="perplexity", model=settings.PERPLEXITY_MODEL).inc(
                response.usage.total_tokens
            )

            return content, metadata

        except Exception as e:
            logger.warning("Perplexity generation failed, falling back to Gemini", error=str(e))

            # Fallback to Gemini
            try:
                response = await self.gemini_client.chat.completions.create(
                    model=settings.GEMINI_MODEL,
                    messages=[
                        {"role": "system", "content": persona.get("system_prompt", "")},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                content = response.choices[0].message.content
                metadata = {
                    "provider": "gemini",
                    "model": settings.GEMINI_MODEL,
                    "tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "cost": 0.0,  # Gemini Flash is free/cheap, treating as 0 for now or implement pricing
                }

                token_usage.labels(provider="gemini", model=settings.GEMINI_MODEL).inc(
                    response.usage.total_tokens
                )

                return content, metadata

            except Exception as e:
                logger.error("Both LLM providers failed", error=str(e))
                generation_errors.labels(provider="all", error_type="provider_failure").inc()
                raise

    async def regenerate_safe_response(self, prompt: str, persona: Dict) -> str:
        """Regenerate response with additional safety instructions"""
        safe_prompt = f"{prompt}\n\nIMPORTANT: Ensure your response is professional, respectful, and appropriate for public discussion."

        response_text, _ = await self.generate_with_llm(safe_prompt, persona, "")
        return response_text

    def calculate_perplexity_cost(self, usage) -> float:
        """Calculate Perplexity API cost"""
        # Perplexity Sonar Small pricing (approximate)
        # $0.20 per 1M tokens
        return (usage.total_tokens * 0.20) / 1_000_000

    def calculate_gemini_cost(self, usage) -> float:
        """Calculate Gemini API cost"""
        # Gemini Flash is free within limits, or very cheap
        return 0.0

    async def save_response(
        self,
        post_id: str,
        persona_id: Optional[str],
        response_text: str,
        metadata: Dict,
        quality_score: float,
        safety_score: float,
        auto_approved: bool = False,
    ) -> str:
        """Save generated response to database"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            response_id = await conn.fetchval(
                """
                INSERT INTO generated_responses (
                    post_id, persona_id, response_text, response_metadata,
                    quality_score, safety_score, approved, cost
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                post_id,
                persona_id,
                response_text,
                json.dumps(metadata),
                quality_score,
                safety_score,
                auto_approved,
                metadata.get("cost", 0),
            )

        return response_id

    async def track_cost(self, organization_id: str, metadata: Dict):
        """Track API usage cost"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Update organization spend
            await conn.execute(
                """
                UPDATE organizations
                SET current_spend = current_spend + $1
                WHERE id = $2
                """,
                metadata.get("cost", 0),
                organization_id,
            )

            # Log to analytics (if using ClickHouse, this would go through message queue)
            await publish_message(
                "analytics.cost",
                {
                    "organization_id": organization_id,
                    "service": metadata["provider"],
                    "operation": "response_generation",
                    "tokens": metadata["tokens"],
                    "cost": metadata["cost"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def close(self):
        """Cleanup resources"""
        if self.perplexity_client:
            await self.perplexity_client.close()
        if self.gemini_client:
            await self.gemini_client.close()
        logger.info("Response generator closed")
