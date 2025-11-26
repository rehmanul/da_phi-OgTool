"""Content moderation using OpenAI Moderation API"""
from typing import Tuple
from openai import AsyncOpenAI
import structlog

from app.config import settings
from app.metrics import moderation_failures

logger = structlog.get_logger()


class ContentModerator:
    """Moderate AI-generated content for safety"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def check(self, text: str) -> Tuple[bool, float]:
        """
        Check if content is safe using OpenAI moderation API

        Returns:
            (is_safe, safety_score) where safety_score is 0.0-1.0
        """
        if not settings.ENABLE_CONTENT_MODERATION:
            return True, 1.0

        try:
            response = await self.client.moderations.create(input=text)
            result = response.results[0]

            is_safe = not result.flagged

            # Calculate composite safety score (inverse of max violation score)
            max_violation = max([
                result.category_scores.hate,
                result.category_scores.hate_threatening,
                result.category_scores.harassment,
                result.category_scores.harassment_threatening,
                result.category_scores.self_harm,
                result.category_scores.self_harm_intent,
                result.category_scores.self_harm_instructions,
                result.category_scores.sexual,
                result.category_scores.sexual_minors,
                result.category_scores.violence,
                result.category_scores.violence_graphic,
            ])

            safety_score = 1.0 - max_violation

            if not is_safe:
                logger.warning(
                    "Content failed moderation",
                    flagged_categories=[
                        cat for cat, flagged in result.categories.__dict__.items() if flagged
                    ],
                    max_violation=max_violation,
                )
                moderation_failures.inc()

            return is_safe, safety_score

        except Exception as e:
            logger.error("Error in content moderation", error=str(e))
            # Fail open but log the error
            return True, 0.5

    async def check_batch(self, texts: list[str]) -> list[Tuple[bool, float]]:
        """Check multiple texts for safety"""
        # OpenAI moderation API supports batch requests
        try:
            response = await self.client.moderations.create(input=texts)

            results = []
            for result in response.results:
                is_safe = not result.flagged

                max_violation = max([
                    result.category_scores.hate,
                    result.category_scores.hate_threatening,
                    result.category_scores.harassment,
                    result.category_scores.harassment_threatening,
                    result.category_scores.self_harm,
                    result.category_scores.self_harm_intent,
                    result.category_scores.self_harm_instructions,
                    result.category_scores.sexual,
                    result.category_scores.sexual_minors,
                    result.category_scores.violence,
                    result.category_scores.violence_graphic,
                ])

                safety_score = 1.0 - max_violation
                results.append((is_safe, safety_score))

            return results

        except Exception as e:
            logger.error("Error in batch moderation", error=str(e))
            return [(True, 0.5)] * len(texts)
