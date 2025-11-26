"""
AI Response Generation with Persona Management
Production-ready response generation for social engagement
"""
import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
import google.generativeai as genai
import structlog

from database.models import Lead, Persona, Response, ResponseTemplate, PersonaType

logger = structlog.get_logger()

class AIResponseGenerator:
    """Advanced AI response generation with persona management"""

    def __init__(self):
        """Initialize AI clients and configurations"""
        self.perplexity_client = None
        self.gemini_model = None

        # Initialize Perplexity
        perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
        if perplexity_key:
            self.perplexity_client = openai.OpenAI(
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai"
            )
            logger.info("Perplexity client initialized for response generation")

        # Initialize Gemini
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini client initialized for response generation")

        # Response configuration
        self.max_retries = 3
        self.temperature = 0.7
        self.max_tokens = 500

    async def generate_response(
        self,
        lead: Lead,
        persona: Persona,
        model: str = "perplexity",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate an AI response for a lead using a specific persona"""
        try:
            # Build the context
            context = self._build_context(lead, persona)

            # Build the prompt
            prompt = self._build_prompt(lead, persona, context, custom_instructions)

            # Generate response
            if model == "perplexity" and self.perplexity_client:
                response_content = await self._generate_perplexity_response(prompt)
            elif model == "gemini" and self.gemini_model:
                response_content = await self._generate_gemini_response(prompt)
            else:
                raise ValueError(f"Model {model} not available")

            # Post-process response
            response_content = self._post_process_response(response_content, persona)

            # Ensure response doesn't exceed persona limits
            if persona.max_response_length:
                response_content = self._truncate_response(
                    response_content,
                    persona.max_response_length
                )

            return {
                "success": True,
                "content": response_content,
                "model": model,
                "persona_id": persona.id,
                "persona_name": persona.name,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "persona_id": persona.id
            }

    def _build_context(self, lead: Lead, persona: Persona) -> Dict[str, Any]:
        """Build context for response generation"""
        context = {
            "platform": lead.platform.value if hasattr(lead.platform, 'value') else str(lead.platform),
            "post_title": lead.title,
            "post_content": lead.content,
            "post_author": lead.author,
            "post_url": lead.url,
            "intent": lead.ai_intent or "general",
            "sentiment": lead.ai_sentiment or "neutral",
            "keywords_matched": [kw.keyword.keyword for kw in lead.keywords] if lead.keywords else []
        }

        # Add platform-specific context
        if context["platform"] == "reddit":
            context.update({
                "subreddit": lead.subreddit,
                "post_karma": lead.post_karma,
                "comment_count": lead.comment_count
            })

        return context

    def _build_prompt(
        self,
        lead: Lead,
        persona: Persona,
        context: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for AI response generation"""
        # Check for matching template
        template = self._find_matching_template(lead, persona)

        if template:
            # Use template as base
            base_prompt = template.template

            # Replace variables
            for variable in template.variables or []:
                if variable in context:
                    base_prompt = base_prompt.replace(f"{{{variable}}}", str(context[variable]))
        else:
            # Build default prompt
            base_prompt = self._build_default_prompt(lead, persona, context)

        # Add persona characteristics
        persona_prompt = f"""
You are responding as {persona.name}, a {persona.type.value if hasattr(persona.type, 'value') else persona.type}.

Background: {persona.background or 'Professional with relevant experience'}
Expertise: {', '.join(persona.expertise) if persona.expertise else 'General knowledge'}
Communication Style: {persona.communication_style or 'Professional and helpful'}
Values: {', '.join(persona.values) if persona.values else 'Integrity, helpfulness'}
Voice Tone: {persona.voice_tone or 'professional'}

{base_prompt}

Response Guidelines:
1. Stay in character as {persona.name}
2. Be authentic and avoid sounding like a bot
3. Provide value and be helpful
4. Keep response concise and engaging
5. Use natural language appropriate for {context['platform']}
"""

        # Add custom instructions if provided
        if custom_instructions:
            persona_prompt += f"\n\nAdditional Instructions: {custom_instructions}"

        # Add call-to-action if enabled
        if persona.include_call_to_action:
            persona_prompt += "\n\nInclude a subtle, non-pushy call-to-action that provides value."

        # Add credentials if enabled
        if persona.include_credentials:
            persona_prompt += f"\n\nBriefly mention relevant credentials or experience when appropriate."

        return persona_prompt

    def _build_default_prompt(
        self,
        lead: Lead,
        persona: Persona,
        context: Dict[str, Any]
    ) -> str:
        """Build default prompt when no template matches"""
        intent_prompts = {
            "question": "The user is asking a question. Provide a helpful, informative answer.",
            "problem": "The user has a problem. Offer a solution or helpful advice.",
            "seeking": "The user is looking for something. Provide relevant recommendations.",
            "negative": "The user is expressing frustration. Show empathy and offer constructive help.",
            "positive": "The user is sharing something positive. Engage positively and add value.",
            "general": "Engage naturally and provide value relevant to the discussion."
        }

        platform_guidelines = {
            "reddit": """
- Follow Reddit etiquette and community norms
- Don't be overly promotional
- Provide value first, mention your solution only if directly relevant
- Be authentic and conversational
""",
            "linkedin": """
- Maintain professional tone
- Focus on business value and insights
- Share expertise and thought leadership
- Network building approach
""",
            "blog": """
- Provide thoughtful, detailed response
- Share relevant expertise
- Add to the discussion meaningfully
- Include relevant examples or case studies
"""
        }

        prompt = f"""
Respond to this {context['platform']} post:

Title: {lead.title}
Content: {lead.content[:1000]}

Post Intent: {context['intent']}
{intent_prompts.get(context['intent'], intent_prompts['general'])}

Platform Guidelines for {context['platform']}:
{platform_guidelines.get(context['platform'], 'Be authentic and helpful')}

Generate a response that:
1. Directly addresses the post's main point
2. Provides genuine value
3. Sounds natural and human
4. Fits the platform's communication style
5. Subtly establishes credibility without being salesy
"""

        return prompt

    def _find_matching_template(
        self,
        lead: Lead,
        persona: Persona
    ) -> Optional[ResponseTemplate]:
        """Find a matching template for the lead"""
        from database.connection import get_db

        with get_db() as db:
            # Look for templates matching intent and persona
            template = db.query(ResponseTemplate).filter(
                ResponseTemplate.persona_id == persona.id,
                ResponseTemplate.intent == lead.ai_intent,
                ResponseTemplate.is_active == True
            ).first()

            if template:
                # Increment usage count
                template.usage_count += 1
                db.commit()
                return template

        return None

    async def _generate_perplexity_response(self, prompt: str) -> str:
        """Generate response using Perplexity AI"""
        try:
            response = self.perplexity_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant generating authentic social media responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Perplexity generation error: {e}")
            raise

    async def _generate_gemini_response(self, prompt: str) -> str:
        """Generate response using Google Gemini"""
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    def _post_process_response(self, response: str, persona: Persona) -> str:
        """Post-process the generated response"""
        # Remove any AI artifacts
        response = re.sub(r'\[.*?\]', '', response)  # Remove bracketed instructions
        response = re.sub(r'\*.*?\*', '', response)  # Remove emphasized instructions
        response = response.strip()

        # Add greeting if configured
        if persona.greeting_template and not response.lower().startswith(('hi', 'hello', 'hey')):
            response = f"{persona.greeting_template}\n\n{response}"

        # Add closing/signature if configured
        if persona.closing_template:
            response = f"{response}\n\n{persona.closing_template}"

        if persona.signature:
            response = f"{response}\n\n{persona.signature}"

        return response

    def _truncate_response(self, response: str, max_length: int) -> str:
        """Truncate response to maximum length while preserving coherence"""
        if len(response) <= max_length:
            return response

        # Try to truncate at sentence boundary
        sentences = response.split('. ')
        truncated = ""

        for sentence in sentences:
            if len(truncated) + len(sentence) + 2 <= max_length:
                truncated += sentence + ". "
            else:
                break

        # If no complete sentences fit, truncate at word boundary
        if not truncated:
            words = response.split()
            truncated = ""
            for word in words:
                if len(truncated) + len(word) + 1 <= max_length:
                    truncated += word + " "
                else:
                    break

        return truncated.strip()

    async def generate_variations(
        self,
        lead: Lead,
        persona: Persona,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate multiple response variations"""
        variations = []

        for i in range(count):
            # Vary temperature for diversity
            original_temp = self.temperature
            self.temperature = 0.5 + (i * 0.2)  # 0.5, 0.7, 0.9

            response = await self.generate_response(
                lead,
                persona,
                custom_instructions=f"Variation {i+1}: Provide a different approach or angle."
            )

            if response["success"]:
                variations.append(response)

            self.temperature = original_temp

        return variations

    async def refine_response(
        self,
        original_response: str,
        feedback: str,
        persona: Persona
    ) -> str:
        """Refine a response based on user feedback"""
        prompt = f"""
Original response:
{original_response}

User feedback:
{feedback}

Please refine the response based on the feedback while maintaining the persona's voice and style.
Persona: {persona.name} ({persona.type})
Voice: {persona.voice_tone}
"""

        if self.perplexity_client:
            refined = await self._generate_perplexity_response(prompt)
        elif self.gemini_model:
            refined = await self._generate_gemini_response(prompt)
        else:
            raise ValueError("No AI model available")

        return self._post_process_response(refined, persona)

# Persona templates for quick setup
PERSONA_TEMPLATES = {
    "founder": {
        "name": "Startup Founder",
        "type": PersonaType.FOUNDER,
        "background": "Serial entrepreneur with multiple successful exits",
        "expertise": ["startups", "product development", "fundraising", "team building"],
        "communication_style": "Direct, passionate, and solution-oriented",
        "values": ["innovation", "growth", "problem-solving"],
        "voice_tone": "enthusiastic",
        "greeting_template": "Hey there!",
        "closing_template": "Happy to chat more if you'd like to connect."
    },
    "marketer": {
        "name": "Marketing Professional",
        "type": PersonaType.MARKETER,
        "background": "Growth marketer with experience in B2B SaaS",
        "expertise": ["growth marketing", "content strategy", "SEO", "paid acquisition"],
        "communication_style": "Data-driven, strategic, and results-focused",
        "values": ["ROI", "customer acquisition", "brand building"],
        "voice_tone": "professional",
        "greeting_template": "Hi!",
        "closing_template": "Hope this helps with your marketing efforts!"
    },
    "technical": {
        "name": "Technical Expert",
        "type": PersonaType.TECHNICAL,
        "background": "Senior software engineer with full-stack expertise",
        "expertise": ["software architecture", "APIs", "cloud infrastructure", "DevOps"],
        "communication_style": "Precise, helpful, and detail-oriented",
        "values": ["code quality", "scalability", "best practices"],
        "voice_tone": "informative",
        "greeting_template": None,
        "closing_template": "Let me know if you need any technical clarification."
    },
    "support": {
        "name": "Customer Success",
        "type": PersonaType.SUPPORT,
        "background": "Customer success manager focused on user satisfaction",
        "expertise": ["customer support", "onboarding", "user experience", "problem resolution"],
        "communication_style": "Empathetic, patient, and solution-focused",
        "values": ["customer satisfaction", "helpfulness", "responsiveness"],
        "voice_tone": "friendly",
        "greeting_template": "Hi there!",
        "closing_template": "I'm here to help if you need anything else!"
    }
}