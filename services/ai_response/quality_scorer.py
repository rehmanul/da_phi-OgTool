"""Response quality scoring algorithm"""
import re
from typing import Dict
import structlog

from app.config import settings
from app.metrics import quality_scores

logger = structlog.get_logger()


class QualityScorer:
    """Calculate quality scores for AI-generated responses"""

    def __init__(self):
        self.promotional_words = {
            'buy', 'purchase', 'discount', 'offer', 'deal', 'sale', 'promo',
            'limited time', 'act now', 'click here', 'sign up now', 'free trial'
        }

        self.spam_indicators = {
            'dm me', 'pm me', 'check my profile', 'link in bio', 'follow me',
            'check out my', 'visit my website'
        }

    async def score(
        self, response: str, post: Dict, persona: Dict
    ) -> float:
        """
        Calculate comprehensive quality score (0.0-1.0)

        Scoring factors:
        - Length appropriateness (0.2)
        - Relevance to post keywords (0.3)
        - Natural language quality (0.2)
        - Authenticity (non-promotional) (0.3)
        """
        if not settings.ENABLE_QUALITY_SCORING:
            return 0.8  # Default acceptable score

        score = 0.0

        # 1. Length appropriateness (0.2)
        score += self._score_length(response)

        # 2. Relevance to post (0.3)
        score += self._score_relevance(response, post)

        # 3. Natural language quality (0.2)
        score += self._score_natural_language(response)

        # 4. Authenticity (0.3)
        score += self._score_authenticity(response)

        # Cap at 1.0
        final_score = min(score, 1.0)

        # Record metric
        quality_scores.observe(final_score)

        logger.debug("Quality score calculated", score=final_score)

        return final_score

    def _score_length(self, response: str) -> float:
        """Score response length appropriateness"""
        word_count = len(response.split())

        # Ideal length: 30-200 words
        if 30 <= word_count <= 200:
            return 0.2
        elif 20 <= word_count < 30 or 200 < word_count <= 300:
            return 0.15
        elif 10 <= word_count < 20 or 300 < word_count <= 400:
            return 0.1
        else:
            return 0.05

    def _score_relevance(self, response: str, post: Dict) -> float:
        """Score relevance to post keywords and content"""
        score = 0.0
        response_lower = response.lower()

        # Check keyword mentions
        keywords = post.get('keyword_matches', [])
        if keywords:
            matches = sum(1 for kw in keywords if kw.lower() in response_lower)
            keyword_score = min(matches * 0.1, 0.15)
            score += keyword_score

        # Check if response addresses post content
        post_content = post.get('content', '').lower()
        if post_content:
            # Extract significant words from post (longer than 4 chars)
            post_words = set(re.findall(r'\b\w{5,}\b', post_content))
            response_words = set(re.findall(r'\b\w{5,}\b', response_lower))

            # Calculate overlap
            if post_words:
                overlap = len(post_words & response_words) / len(post_words)
                score += min(overlap * 0.15, 0.15)

        return score

    def _score_natural_language(self, response: str) -> float:
        """Score natural language quality"""
        score = 0.0

        # Check capitalization ratio (excessive caps is bad)
        if len(response) > 0:
            caps_ratio = sum(1 for c in response if c.isupper()) / len(response)
            if caps_ratio < 0.15:  # Less than 15% caps is good
                score += 0.1

        # Check exclamation marks (excessive is bad)
        exclamations = response.count('!')
        if exclamations == 0:
            score += 0.05
        elif exclamations <= 2:
            score += 0.03

        # Check question engagement (1-2 questions is good)
        questions = response.count('?')
        if 1 <= questions <= 2:
            score += 0.05

        return score

    def _score_authenticity(self, response: str) -> float:
        """Score authenticity (penalize promotional/spam language)"""
        score = 0.3  # Start with full authenticity score
        response_lower = response.lower()

        # Penalize promotional words
        promo_count = sum(
            1 for word in self.promotional_words
            if word in response_lower
        )
        score -= min(promo_count * 0.1, 0.15)

        # Heavily penalize spam indicators
        spam_count = sum(
            1 for phrase in self.spam_indicators
            if phrase in response_lower
        )
        score -= min(spam_count * 0.2, 0.3)

        # Penalize URLs (unless just one)
        url_count = len(re.findall(r'https?://\S+', response))
        if url_count == 0:
            pass  # No penalty
        elif url_count == 1:
            score -= 0.05  # Small penalty for one URL
        else:
            score -= 0.15  # Larger penalty for multiple URLs

        return max(score, 0.0)  # Don't go negative
