"""Production prompt engineering for context-aware response generation"""
from typing import Dict, List
from jinja2 import Template
import structlog

logger = structlog.get_logger()


class PromptBuilder:
    """Build optimized prompts for response generation"""

    def __init__(self):
        self.response_template = Template("""
You are responding to a {{ platform }} post as {{ persona_name }}.

PERSONA PROFILE:
{{ persona_description }}

VOICE GUIDELINES:
- Tone: {{ tone }}
- Style: {{ style }}
- Formality: {{ formality }}
{% if avoid_words %}
- Words to avoid: {{ avoid_words }}
{% endif %}

POST CONTEXT:
Title: {{ post_title }}
Content: {{ post_content }}
Author: {{ post_author }}
Engagement: {{ engagement_score }} score, {{ comment_count }} comments
Keywords matched: {{ keywords }}

{% if knowledge %}
RELEVANT KNOWLEDGE BASE:
{% for doc in knowledge %}
{{ loop.index }}. {{ doc.title }}
   {{ doc.content[:300] }}...
   (Source: {{ doc.source }})
{% endfor %}
{% endif %}

{% if example_responses %}
EXAMPLE RESPONSES IN YOUR VOICE:
{% for example in example_responses %}
User: {{ example.input }}
You: {{ example.output }}

{% endfor %}
{% endif %}

INSTRUCTIONS:
Write a helpful, authentic response that:
1. Directly addresses the user's question or concern
2. Provides actionable value or insights
3. Uses information from the knowledge base when relevant
4. Maintains your voice profile (tone, style, formality)
5. Is conversational and human-like (not robotic or overly formal)
6. Keeps it concise (2-4 paragraphs, 50-150 words ideal)
7. Avoids being overly promotional or sales-y
8. Sounds like a genuine community member, not a brand account

{% if platform == 'reddit' %}
REDDIT-SPECIFIC GUIDELINES:
- Be genuine and avoid sounding like marketing
- Don't mention your company/product unless directly relevant to the question
- Add value first, promote second (if at all)
- Use Reddit's casual, conversational tone
- Don't use emojis excessively
- It's okay to admit "I don't know" or "I'm not sure"
- Build genuine connections, not just promotional responses
{% elif platform == 'linkedin' %}
LINKEDIN-SPECIFIC GUIDELINES:
- Professional but warm and approachable tone
- Can be more business-focused than Reddit
- Share expertise and professional insights
- Appropriate to mention relevant professional experience
- Can use professional emojis sparingly
- Focus on adding value to professional discussions
{% endif %}

Generate your response now (do not include meta-commentary, just the response itself):
        """)

    def build_response_prompt(
        self,
        post: Dict,
        persona: Dict,
        knowledge: List[Dict],
        platform: str,
    ) -> str:
        """Build complete prompt for response generation"""

        voice_profile = persona.get("voice_profile", {})

        context = {
            "platform": platform,
            "persona_name": persona.get("name", "Assistant"),
            "persona_description": voice_profile.get("description", "A helpful assistant"),
            "tone": voice_profile.get("tone", "professional"),
            "style": voice_profile.get("style", "informative"),
            "formality": voice_profile.get("formality", "balanced"),
            "avoid_words": ", ".join(voice_profile.get("avoid_words", [])),
            "post_title": post.get("title", "")[:200],
            "post_content": post.get("content", "")[:1000],  # Limit for token usage
            "post_author": post.get("author", "User"),
            "engagement_score": int(post.get("engagement_score", 0)),
            "comment_count": post.get("comment_count", 0),
            "keywords": ", ".join(post.get("keyword_matches", [])[:5]),
            "knowledge": [
                {
                    "title": doc["title"],
                    "content": doc["content"][:300],  # Limit length
                    "source": doc.get("source", "Internal docs"),
                }
                for doc in knowledge[:3]  # Top 3 most relevant docs
            ],
            "example_responses": persona.get("example_responses", [])[:2],  # Top 2 examples
        }

        prompt = self.response_template.render(**context)

        logger.debug("Prompt built", prompt_length=len(prompt), platform=platform)

        return prompt

    def build_training_prompt(self, examples: List[Dict]) -> str:
        """Build prompt for fine-tuning examples"""
        prompt_parts = ["Here are examples of ideal responses in this persona's voice:\n"]

        for i, example in enumerate(examples[:10], 1):  # Max 10 examples
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Input: {example['input']}")
            prompt_parts.append(f"Response: {example['output']}\n")

        return "\n".join(prompt_parts)

    def build_knowledge_extraction_prompt(self, content: str) -> str:
        """Build prompt for extracting key information from documents"""
        return f"""
Extract the key information, facts, and insights from the following content.
Focus on:
- Main topics and themes
- Specific facts, statistics, or data points
- Actionable advice or recommendations
- Technical details or specifications
- Common questions and their answers

Content:
{content[:4000]}

Extracted information (be concise and organized):
        """

    def build_improvement_prompt(self, original_response: str, feedback: str) -> str:
        """Build prompt for improving a response based on feedback"""
        return f"""
Here is an AI-generated response that needs improvement:

ORIGINAL RESPONSE:
{original_response}

FEEDBACK/ISSUES:
{feedback}

Please rewrite this response to address the feedback while maintaining:
- The core helpful intent
- Professional and authentic tone
- Conciseness (50-150 words)

IMPROVED RESPONSE:
        """
