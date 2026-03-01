"""LLM service for content moderation."""

import asyncio
import os
from typing import Optional
import httpx

from app.core.config import settings


class LLMService:
    """
    LLM service for content moderation.

    Supports multiple LLM providers:
    - Anthropic Claude (recommended)
    - OpenAI GPT-4
    - Local LLM fallback

    Configuration via environment variables:
    - LLM_PROVIDER: "anthropic" | "openai" | "local" (default: "anthropic")
    - ANTHROPIC_API_KEY: Claude API key
    - OPENAI_API_KEY: OpenAI API key
    - LOCAL_LLM_URL: Local LLM endpoint URL
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "default",
        provider: str | None = None,
    ):
        self.provider = provider or settings.llm_provider
        self.api_key = api_key or self._get_api_key_for_provider()
        self.model = model or self._get_default_model_for_provider()
        self.timeout = 30.0  # seconds
        self.test_mode = settings.llm_test_mode

    def _get_api_key_for_provider(self) -> str | None:
        """Get API key based on provider."""
        if self.provider == "anthropic":
            return settings.anthropic_api_key
        elif self.provider == "openai":
            return settings.openai_api_key
        return None

    def _get_default_model_for_provider(self) -> str:
        """Get default model for provider."""
        if self.provider == "anthropic":
            return settings.model if hasattr(settings, 'model') else "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            return "gpt-4o"
        return "default"

    async def review_content(self, content: str) -> dict:
        """
        Review content using LLM.

        Args:
            content: The content text to review

        Returns:
            dict with keys:
                - risk: "high" or "low"
                - confidence: 0-1 float
                - notes: optional explanation
                - categories: list of detected categories
        """
        if self.test_mode:
            # Return mock response in test mode
            return self._mock_review(content)

        if self.provider == "anthropic":
            return await self._anthropic_review(content)
        elif self.provider == "openai":
            return await self._openai_review(content)
        else:
            return self._mock_review(content)

    def _mock_review(self, content: str) -> dict:
        """Mock review for testing."""
        prohibited_keywords = [
            "bet", "gambling", "casino",
            "election", "vote", "politician",
            "church", "temple", "religion",
            "football", "soccer", "match score",
        ]

        content_lower = content.lower()
        matches = [kw for kw in prohibited_keywords if kw in content_lower]

        if matches:
            return {
                "risk": "high",
                "confidence": 0.7,
                "notes": f"Potentially prohibited keywords: {', '.join(matches)}",
                "categories": ["prohibited_keywords"],
            }
        else:
            return {
                "risk": "low",
                "confidence": 0.9,
                "notes": "No obvious prohibited content detected",
                "categories": [],
            }

    async def _anthropic_review(self, content: str) -> dict:
        """Review content using Anthropic Claude API."""
        prompt = f"""You are a content moderation AI for a Vietnamese prediction market platform.
Review the following content and determine if it contains:
1. Political content (elections, government, politicians)
2. Religious content
3. Sports betting content
4. Adult/explicit content
5. Violence or harm
6. Spam or fraud
7. Any other prohibited content

Content: {content}

Respond in JSON format:
{{
    "risk": "high" or "low",
    "confidence": 0.0-1.0,
    "categories": ["list of detected categories"],
    "explanation": "brief explanation"
}}"""

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # Parse LLM response
                content_text = result["content"][0]["text"]
                # Extract JSON from response
                import json
                try:
                    # Try to extract JSON from response
                    start_idx = content_text.find("{")
                    end_idx = content_text.rfind("}") + 1
                    json_str = content_text[start_idx:end_idx]
                    return json.loads(json_str)
                except:
                    return self._mock_review(content)
        except Exception as e:
            print(f"[LLM] Anthropic API error: {e}")
            return self._mock_review(content)

    async def _openai_review(self, content: str) -> dict:
        """Review content using OpenAI GPT-4 API."""
        prompt = f"""You are a content moderation AI for a Vietnamese prediction market platform.
Review the following content and determine if it contains prohibited content:
- Political content (elections, government, politicians)
- Religious content
- Sports betting content
- Adult/explicit content
- Violence or harm
- Spam or fraud

Content: {content}

Respond in JSON format:
{{
    "risk": "high" or "low",
    "confidence": 0.0-1.0,
    "categories": ["list of detected categories"],
    "explanation": "brief explanation"
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a content moderation AI."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                import json
                content_text = result["choices"][0]["message"]["content"]
                return json.loads(content_text)
        except Exception as e:
            print(f"[LLM] OpenAI API error: {e}")
            return self._mock_review(content)

    async def classify_content(self, content: str) -> dict:
        """
        Classify content into categories.

        Args:
            content: The content text to classify

        Returns:
            dict with category predictions
        """
        if self.test_mode:
            return self._mock_classify(content)

        if self.provider == "anthropic":
            return await self._anthropic_classify(content)
        elif self.provider == "openai":
            return await self._openai_classify(content)
        else:
            return self._mock_classify(content)

    def _mock_classify(self, content: str) -> dict:
        """Mock classification for testing."""
        categories = ["tech", "business", "culture", "academic"]

        # Simple keyword-based classification
        content_lower = content.lower()
        scores = {}
        for cat in categories:
            if cat in content_lower:
                scores[cat] = 0.8
            else:
                scores[cat] = 0.2

        primary = max(scores, key=scores.get)
        return {
            "primary_category": primary,
            "confidence": scores[primary],
            "all_categories": scores,
        }

    async def _anthropic_classify(self, content: str) -> dict:
        """Classify content using Anthropic Claude API."""
        prompt = f"""Classify the following content into one of these categories:
- tech (technology, software, AI, gadgets)
- business (finance, economics, startups, markets)
- culture (arts, entertainment, lifestyle, traditions)
- academic (research, science, education, studies)

Content: {content}

Respond in JSON format:
{{
    "primary_category": "category name",
    "confidence": 0.0-1.0,
    "all_categories": {{
        "tech": 0.0-1.0,
        "business": 0.0-1.0,
        "culture": 0.0-1.0,
        "academic": 0.0-1.0
    }}
}}"""

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                import json
                content_text = result["content"][0]["text"]
                start_idx = content_text.find("{")
                end_idx = content_text.rfind("}") + 1
                json_str = content_text[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            print(f"[LLM] Anthropic classification error: {e}")
            return self._mock_classify(content)

    async def _openai_classify(self, content: str) -> dict:
        """Classify content using OpenAI GPT-4 API."""
        prompt = f"""Classify the following content into one of these categories:
- tech (technology, software, AI, gadgets)
- business (finance, economics, startups, markets)
- culture (arts, entertainment, lifestyle, traditions)
- academic (research, science, education, studies)

Content: {content}

Respond in JSON format:
{{
    "primary_category": "category name",
    "confidence": 0.0-1.0,
    "all_categories": {{
        "tech": 0.0-1.0,
        "business": 0.0-1.0,
        "culture": 0.0-1.0,
        "academic": 0.0-1.0
    }}
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a content classification AI."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                import json
                content_text = result["choices"][0]["message"]["content"]
                return json.loads(content_text)
        except Exception as e:
            print(f"[LLM] OpenAI classification error: {e}")
            return self._mock_classify(content)

    async def detect_spam(self, content: str, user_recent_contents: list[str] | None = None) -> dict:
        """
        Detect if content is spam.

        Args:
            content: The content to check
            user_recent_contents: Recent contents from same user

        Returns:
            dict with spam detection results
        """
        if self.test_mode:
            return self._mock_detect_spam(content, user_recent_contents)

        if self.provider == "anthropic":
            return await self._anthropic_detect_spam(content, user_recent_contents)
        elif self.provider == "openai":
            return await self._openai_detect_spam(content, user_recent_contents)
        else:
            return self._mock_detect_spam(content, user_recent_contents)

    def _mock_detect_spam(self, content: str, user_recent_contents: list[str] | None = None) -> dict:
        """Mock spam detection for testing."""
        is_spam = False
        reasons = []

        # Check for excessive length
        if len(content) > 500:
            reasons.append("excessive_length")

        # Check for repetitive patterns
        if user_recent_contents:
            similar_count = sum(1 for rc in user_recent_contents if content[:50] in rc)
            if similar_count >= 3:
                reasons.append("repetitive_content")
                is_spam = True

        return {
            "is_spam": is_spam,
            "confidence": 0.8 if is_spam else 0.5,
            "reasons": reasons,
        }

    async def _anthropic_detect_spam(self, content: str, user_recent_contents: list[str] | None = None) -> dict:
        """Detect spam using Anthropic Claude API."""
        recent_context = ""
        if user_recent_contents:
            recent_context = "User's recent content:\n" + "\n".join(user_recent_contents[:5])

        prompt = f"""Determine if the following content is spam. Consider:
- Repetitive or copy-pasted content
- Promotional or advertising content
- Irrelevant or off-topic content
- Excessive links or contact information
- Gibberish or nonsensical text

{recent_context}

Content to evaluate: {content}

Respond in JSON format:
{{
    "is_spam": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["reason1", "reason2"]
}}"""

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                import json
                content_text = result["content"][0]["text"]
                start_idx = content_text.find("{")
                end_idx = content_text.rfind("}") + 1
                json_str = content_text[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            print(f"[LLM] Anthropic spam detection error: {e}")
            return self._mock_detect_spam(content, user_recent_contents)

    async def _openai_detect_spam(self, content: str, user_recent_contents: list[str] | None = None) -> dict:
        """Detect spam using OpenAI GPT-4 API."""
        recent_context = ""
        if user_recent_contents:
            recent_context = "User's recent content:\n" + "\n".join(user_recent_contents[:5])

        prompt = f"""Determine if the following content is spam. Consider:
- Repetitive or copy-pasted content
- Promotional or advertising content
- Irrelevant or off-topic content
- Excessive links or contact information
- Gibberish or nonsensical text

{recent_context}

Content to evaluate: {content}

Respond in JSON format:
{{
    "is_spam": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["reason1", "reason2"]
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a spam detection AI."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                import json
                content_text = result["choices"][0]["message"]["content"]
                return json.loads(content_text)
        except Exception as e:
            print(f"[LLM] OpenAI spam detection error: {e}")
            return self._mock_detect_spam(content, user_recent_contents)
