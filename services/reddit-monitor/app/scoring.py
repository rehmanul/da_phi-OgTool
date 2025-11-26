"""
Scoring algorithms for post relevance and engagement
"""
import math
from typing import List, Dict
import re


def calculate_relevance_score(text: str, keywords: List[Dict], title: str = "") -> float:
    """
    Calculate relevance score based on keyword matches and position

    Score factors:
    - Number of unique keyword matches
    - Keyword priority
    - Position in text (title > early content > late content)
    - Keyword density
    - Match confidence (exact vs fuzzy)
    """
    if not keywords:
        return 0.0

    text_lower = text.lower()
    title_lower = title.lower()

    # Base score from keyword count
    unique_keywords = len(set(k["keyword_id"] for k in keywords))
    base_score = min(unique_keywords * 0.2, 0.6)  # Max 0.6 from count

    # Position bonus
    position_score = 0.0
    for keyword in keywords:
        kw = keyword["keyword"].lower()

        # Title match = highest bonus
        if kw in title_lower:
            position_score += 0.15
        # Early in text (first 200 chars)
        elif kw in text_lower[:200]:
            position_score += 0.1
        # Elsewhere in text
        elif kw in text_lower:
            position_score += 0.05

    position_score = min(position_score, 0.3)  # Max 0.3 from position

    # Priority bonus (normalized)
    avg_priority = sum(k["priority"] for k in keywords) / len(keywords)
    priority_score = (avg_priority / 100) * 0.1  # Max 0.1 from priority

    # Confidence bonus (exact matches > fuzzy)
    avg_confidence = sum(k.get("confidence", 1.0) for k in keywords) / len(keywords)
    confidence_score = avg_confidence * 0.1  # Max 0.1 from confidence

    # Keyword density
    word_count = len(text.split())
    if word_count > 0:
        density = sum(text_lower.count(k["keyword"].lower()) for k in keywords) / word_count
        density_score = min(density * 2, 0.1)  # Max 0.1 from density
    else:
        density_score = 0.0

    total_score = base_score + position_score + priority_score + confidence_score + density_score

    # Cap at 1.0
    return min(total_score, 1.0)


def calculate_engagement_score(upvotes: int, comments: int, post_age_hours: float) -> float:
    """
    Calculate engagement score based on votes, comments, and recency

    Uses a time-decay model to favor recent, active posts
    """
    # Normalize upvotes (log scale to handle large numbers)
    upvote_score = math.log1p(max(upvotes, 0)) * 5

    # Comments are more valuable than upvotes
    comment_score = math.log1p(comments) * 8

    # Time decay factor (exponential decay)
    # Posts lose value over time, with half-life of 12 hours
    time_decay = math.exp(-post_age_hours / 12)

    raw_score = (upvote_score + comment_score) * time_decay

    # Normalize to 0-100 scale (using tanh for soft capping)
    normalized_score = math.tanh(raw_score / 50) * 100

    return max(0.0, min(100.0, normalized_score))


def calculate_sentiment_score(text: str) -> float:
    """
    Basic sentiment analysis (-1 to 1)
    Production version should use a proper sentiment model
    """
    # Positive words
    positive_words = {
        "good", "great", "excellent", "amazing", "love", "best", "awesome",
        "fantastic", "wonderful", "perfect", "helpful", "thanks", "recommend",
        "solved", "works", "easy", "fast", "reliable"
    }

    # Negative words
    negative_words = {
        "bad", "terrible", "awful", "hate", "worst", "horrible", "useless",
        "broken", "issue", "problem", "error", "fail", "slow", "difficult",
        "buggy", "crash", "disappointed", "frustrated"
    }

    words = re.findall(r'\b\w+\b', text.lower())

    positive_count = sum(1 for w in words if w in positive_words)
    negative_count = sum(1 for w in words if w in negative_words)

    total = positive_count + negative_count
    if total == 0:
        return 0.0

    sentiment = (positive_count - negative_count) / total
    return sentiment


def calculate_priority_level(
    relevance_score: float,
    engagement_score: float,
    sentiment_score: float,
    keyword_priority: float
) -> str:
    """
    Determine priority level based on multiple factors
    Returns: urgent, high, medium, or low
    """
    # Weighted composite score
    composite = (
        relevance_score * 0.4 +
        (engagement_score / 100) * 0.3 +
        (sentiment_score + 1) / 2 * 0.1 +  # Normalize sentiment to 0-1
        (keyword_priority / 100) * 0.2
    )

    if composite >= 0.8:
        return "urgent"
    elif composite >= 0.6:
        return "high"
    elif composite >= 0.4:
        return "medium"
    else:
        return "low"
