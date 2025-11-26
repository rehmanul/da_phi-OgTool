"""
Production keyword matching engine with fuzzy matching and priority handling
"""
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher
import structlog

logger = structlog.get_logger()


class KeywordMatcher:
    """Advanced keyword matching with fuzzy logic and context awareness"""

    def __init__(self, fuzzy_threshold: float = 0.85):
        self.keywords: Dict[str, Dict] = {}  # keyword -> metadata
        self.org_keywords: Dict[str, Set[str]] = {}  # org_id -> set of keywords
        self.fuzzy_threshold = fuzzy_threshold
        self.compiled_patterns: Dict[str, re.Pattern] = {}

    def add_keyword(
        self, keyword: str, keyword_id: str, organization_id: str, priority: int = 50
    ):
        """Add a keyword to the matcher"""
        keyword_lower = keyword.lower()

        self.keywords[keyword_lower] = {
            "id": keyword_id,
            "original": keyword,
            "organization_id": organization_id,
            "priority": priority,
        }

        if organization_id not in self.org_keywords:
            self.org_keywords[organization_id] = set()
        self.org_keywords[organization_id].add(keyword_lower)

        # Compile regex pattern for exact and word boundary matching
        pattern = rf"\b{re.escape(keyword_lower)}\b"
        self.compiled_patterns[keyword_lower] = re.compile(pattern, re.IGNORECASE)

    def remove_keyword(self, keyword: str, organization_id: str):
        """Remove a keyword"""
        keyword_lower = keyword.lower()
        if keyword_lower in self.keywords:
            del self.keywords[keyword_lower]
            if organization_id in self.org_keywords:
                self.org_keywords[organization_id].discard(keyword_lower)
            if keyword_lower in self.compiled_patterns:
                del self.compiled_patterns[keyword_lower]

    def match(self, text: str, organization_id: str) -> List[Dict]:
        """
        Match text against keywords for a specific organization
        Returns list of matched keywords with metadata
        """
        if organization_id not in self.org_keywords:
            return []

        text_lower = text.lower()
        matches = []
        matched_keywords = set()

        org_keywords = self.org_keywords[organization_id]

        # Exact and word boundary matches
        for keyword in org_keywords:
            if keyword in matched_keywords:
                continue

            pattern = self.compiled_patterns.get(keyword)
            if pattern and pattern.search(text_lower):
                keyword_data = self.keywords[keyword]
                matches.append(
                    {
                        "keyword": keyword_data["original"],
                        "keyword_id": keyword_data["id"],
                        "priority": keyword_data["priority"],
                        "match_type": "exact",
                        "confidence": 1.0,
                    }
                )
                matched_keywords.add(keyword)

        # Fuzzy matching for near misses
        words = set(re.findall(r"\b\w+\b", text_lower))
        for keyword in org_keywords:
            if keyword in matched_keywords:
                continue

            # Check for fuzzy matches
            for word in words:
                if len(word) < 4:  # Skip short words for fuzzy matching
                    continue

                similarity = SequenceMatcher(None, keyword, word).ratio()
                if similarity >= self.fuzzy_threshold:
                    keyword_data = self.keywords[keyword]
                    matches.append(
                        {
                            "keyword": keyword_data["original"],
                            "keyword_id": keyword_data["id"],
                            "priority": keyword_data["priority"],
                            "match_type": "fuzzy",
                            "confidence": similarity,
                        }
                    )
                    matched_keywords.add(keyword)
                    break

        # Phrase matching for multi-word keywords
        for keyword in org_keywords:
            if " " in keyword and keyword not in matched_keywords:
                if keyword in text_lower:
                    keyword_data = self.keywords[keyword]
                    matches.append(
                        {
                            "keyword": keyword_data["original"],
                            "keyword_id": keyword_data["id"],
                            "priority": keyword_data["priority"],
                            "match_type": "phrase",
                            "confidence": 1.0,
                        }
                    )
                    matched_keywords.add(keyword)

        # Sort by priority (descending)
        matches.sort(key=lambda x: x["priority"], reverse=True)

        return matches

    def match_with_context(self, text: str, organization_id: str, context_window: int = 50) -> List[Dict]:
        """
        Match keywords and extract surrounding context
        """
        matches = self.match(text, organization_id)

        for match in matches:
            keyword = match["keyword"]
            # Find keyword position and extract context
            pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            search_result = pattern.search(text)

            if search_result:
                start = max(0, search_result.start() - context_window)
                end = min(len(text), search_result.end() + context_window)
                match["context"] = text[start:end].strip()
                match["position"] = search_result.start()

        return matches

    def get_keyword_count(self) -> int:
        """Get total number of keywords"""
        return len(self.keywords)

    def get_org_keyword_count(self, organization_id: str) -> int:
        """Get keyword count for an organization"""
        return len(self.org_keywords.get(organization_id, set()))
