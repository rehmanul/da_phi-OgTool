"""
Production Lead Scoring Algorithm
Sophisticated scoring based on relevance, engagement, and opportunity
"""
import re
from typing import Dict, List, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class LeadScorer:
    """Advanced lead scoring system"""

    def __init__(self):
        """Initialize scoring weights and configurations"""
        # Scoring weights
        self.weights = {
            'relevance': 0.4,    # How well it matches keywords
            'engagement': 0.3,   # Community engagement level
            'opportunity': 0.3   # Business opportunity potential
        }

        # Intent multipliers
        self.intent_multipliers = {
            'seeking': 1.5,      # Looking for solutions
            'problem': 1.3,      # Has a problem to solve
            'question': 1.2,     # Asking questions
            'negative': 1.1,     # Complaining (opportunity)
            'positive': 0.9,     # Happy (less opportunity)
            'general': 1.0       # Neutral
        }

        # Engagement thresholds
        self.engagement_thresholds = {
            'reddit': {
                'high_karma': 100,
                'medium_karma': 50,
                'high_comments': 20,
                'medium_comments': 10
            },
            'linkedin': {
                'high_reactions': 50,
                'medium_reactions': 20,
                'high_comments': 10,
                'medium_comments': 5
            }
        }

        # Opportunity indicators
        self.opportunity_keywords = {
            'high': [
                'looking for', 'need help', 'recommendations', 'suggest',
                'alternatives', 'solution', 'tool', 'software', 'platform',
                'service', 'hire', 'freelance', 'consultant', 'agency',
                'budget', 'invest', 'purchase', 'buy', 'subscribe'
            ],
            'medium': [
                'problem', 'issue', 'challenge', 'difficult', 'struggle',
                'frustrated', 'annoyed', 'confused', 'wondering', 'curious',
                'interested', 'considering', 'research', 'compare'
            ],
            'low': [
                'free', 'cheap', 'diy', 'myself', 'hobby', 'learning',
                'student', 'personal', 'fun', 'experiment'
            ]
        }

        # Urgency indicators
        self.urgency_keywords = [
            'urgent', 'asap', 'immediately', 'now', 'today',
            'deadline', 'quickly', 'fast', 'emergency', 'critical'
        ]

        # Business indicators
        self.business_keywords = [
            'company', 'business', 'startup', 'enterprise', 'team',
            'client', 'customer', 'revenue', 'growth', 'scale',
            'productivity', 'efficiency', 'roi', 'kpi', 'metric'
        ]

    def score_lead(self, lead: Any, keywords: List[str]) -> Dict[str, float]:
        """
        Score a lead based on multiple factors
        Returns dict with individual scores and total
        """
        try:
            # Calculate individual scores
            relevance_score = self.calculate_relevance_score(lead, keywords)
            engagement_score = self.calculate_engagement_score(lead)
            opportunity_score = self.calculate_opportunity_score(lead)

            # Apply intent multiplier
            intent_multiplier = self.intent_multipliers.get(
                lead.ai_intent or 'general',
                1.0
            )

            # Calculate weighted total
            total_score = (
                (relevance_score * self.weights['relevance']) +
                (engagement_score * self.weights['engagement']) +
                (opportunity_score * self.weights['opportunity'])
            ) * intent_multiplier

            # Ensure scores are between 0 and 1
            total_score = min(1.0, max(0.0, total_score))

            return {
                'relevance': round(relevance_score, 3),
                'engagement': round(engagement_score, 3),
                'opportunity': round(opportunity_score, 3),
                'total': round(total_score, 3)
            }

        except Exception as e:
            logger.error(f"Error scoring lead: {e}")
            return {
                'relevance': 0.0,
                'engagement': 0.0,
                'opportunity': 0.0,
                'total': 0.0
            }

    def calculate_relevance_score(self, lead: Any, keywords: List[str]) -> float:
        """Calculate how relevant the lead is to keywords"""
        score = 0.0
        text = f"{lead.title} {lead.content}".lower()

        # Exact keyword matches
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Title matches worth more
            if keyword_lower in lead.title.lower():
                score += 0.4

            # Count occurrences in content
            occurrences = text.count(keyword_lower)
            if occurrences > 0:
                # Diminishing returns for multiple occurrences
                score += min(0.3, occurrences * 0.1)

            # Check for variations (plural, verb forms)
            if self._check_keyword_variations(keyword_lower, text):
                score += 0.1

        # Contextual relevance
        if self._check_contextual_relevance(text, keywords):
            score += 0.2

        # Recency bonus
        if lead.posted_at:
            hours_old = (datetime.utcnow() - lead.posted_at).total_seconds() / 3600
            if hours_old < 6:
                score += 0.2
            elif hours_old < 24:
                score += 0.1
            elif hours_old < 72:
                score += 0.05

        return min(1.0, score)

    def calculate_engagement_score(self, lead: Any) -> float:
        """Calculate engagement level of the lead"""
        score = 0.0
        platform = lead.platform.value if hasattr(lead.platform, 'value') else str(lead.platform)

        if platform == 'reddit':
            thresholds = self.engagement_thresholds['reddit']

            # Karma score
            if lead.post_karma:
                if lead.post_karma >= thresholds['high_karma']:
                    score += 0.4
                elif lead.post_karma >= thresholds['medium_karma']:
                    score += 0.3
                else:
                    score += 0.1

            # Comment count
            if lead.comment_count:
                if lead.comment_count >= thresholds['high_comments']:
                    score += 0.3
                elif lead.comment_count >= thresholds['medium_comments']:
                    score += 0.2
                else:
                    score += 0.1

            # Upvote ratio
            if lead.upvote_ratio:
                score += lead.upvote_ratio * 0.3

        elif platform == 'linkedin':
            # LinkedIn engagement metrics would go here
            score = 0.5  # Default medium engagement

        else:
            # Default for other platforms
            score = 0.3

        return min(1.0, score)

    def calculate_opportunity_score(self, lead: Any) -> float:
        """Calculate business opportunity potential"""
        score = 0.0
        text = f"{lead.title} {lead.content}".lower()

        # Check high opportunity keywords
        high_matches = sum(1 for kw in self.opportunity_keywords['high'] if kw in text)
        if high_matches > 0:
            score += min(0.5, high_matches * 0.15)

        # Check medium opportunity keywords
        medium_matches = sum(1 for kw in self.opportunity_keywords['medium'] if kw in text)
        if medium_matches > 0:
            score += min(0.3, medium_matches * 0.1)

        # Check low opportunity keywords (negative impact)
        low_matches = sum(1 for kw in self.opportunity_keywords['low'] if kw in text)
        if low_matches > 0:
            score -= min(0.2, low_matches * 0.05)

        # Urgency bonus
        urgency_matches = sum(1 for kw in self.urgency_keywords if kw in text)
        if urgency_matches > 0:
            score += min(0.2, urgency_matches * 0.1)

        # Business context bonus
        business_matches = sum(1 for kw in self.business_keywords if kw in text)
        if business_matches > 0:
            score += min(0.3, business_matches * 0.1)

        # Author influence (for Reddit)
        if hasattr(lead, 'post_karma') and lead.post_karma:
            if lead.post_karma > 10000:
                score += 0.2
            elif lead.post_karma > 1000:
                score += 0.1

        # Subreddit quality (for Reddit)
        if hasattr(lead, 'subreddit') and lead.subreddit:
            quality_subreddits = [
                'entrepreneur', 'startups', 'saas', 'business',
                'smallbusiness', 'marketing', 'webdev', 'programming'
            ]
            if lead.subreddit.lower() in quality_subreddits:
                score += 0.2

        return min(1.0, max(0.0, score))

    def _check_keyword_variations(self, keyword: str, text: str) -> bool:
        """Check for variations of a keyword"""
        variations = [
            keyword + 's',      # Plural
            keyword + 'ing',    # Present continuous
            keyword + 'ed',     # Past tense
            keyword + 'er',     # Comparative
            keyword + 'est',    # Superlative
        ]

        return any(var in text for var in variations)

    def _check_contextual_relevance(self, text: str, keywords: List[str]) -> bool:
        """Check if keywords appear in relevant context"""
        # Industry-specific context words
        context_words = [
            'tool', 'software', 'platform', 'service', 'solution',
            'app', 'application', 'system', 'product', 'feature'
        ]

        # Check if keywords appear near context words
        for keyword in keywords:
            for context_word in context_words:
                # Simple proximity check (within 50 characters)
                pattern = f"{keyword}.{{0,50}}{context_word}|{context_word}.{{0,50}}{keyword}"
                if re.search(pattern, text, re.IGNORECASE):
                    return True

        return False

    def calculate_trend_score(self, leads: List[Any], time_window_hours: int = 24) -> float:
        """Calculate trending score based on multiple leads"""
        if not leads:
            return 0.0

        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_leads = [l for l in leads if l.found_at >= cutoff_time]

        if len(recent_leads) < 3:
            return 0.0

        # Calculate velocity (leads per hour)
        velocity = len(recent_leads) / time_window_hours

        # Calculate average engagement
        avg_engagement = sum(l.engagement_score for l in recent_leads) / len(recent_leads)

        # Trend score combines velocity and engagement
        trend_score = min(1.0, (velocity * 0.1) + (avg_engagement * 0.5))

        return trend_score

    def recalculate_scores(self, lead: Any, additional_context: Dict[str, Any]) -> Dict[str, float]:
        """Recalculate scores with additional context"""
        # This could be used when we have more information
        # like user engagement, response rates, etc.
        base_scores = self.score_lead(lead, additional_context.get('keywords', []))

        # Apply additional context modifiers
        if additional_context.get('user_responded'):
            base_scores['opportunity'] *= 1.2

        if additional_context.get('multiple_interactions'):
            base_scores['engagement'] *= 1.3

        # Recalculate total
        base_scores['total'] = (
            (base_scores['relevance'] * self.weights['relevance']) +
            (base_scores['engagement'] * self.weights['engagement']) +
            (base_scores['opportunity'] * self.weights['opportunity'])
        )

        return base_scores