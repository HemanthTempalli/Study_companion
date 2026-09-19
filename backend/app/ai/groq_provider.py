"""AI Provider abstraction — Groq implementation with usage tracking.

Provides generate_text(), generate_structured(), evaluate_answer() — the rest
of the app never calls Groq directly.
"""

import json
import time
import uuid
import logging
from typing import Optional, Type
from pydantic import BaseModel

from groq import Groq, APIError, RateLimitError, APITimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Raised when the AI provider fails."""
    def __init__(self, message: str, retryable: bool = False):
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class UsageStats:
    def __init__(self):
        self.model = ""
        self.feature = ""
        self.latency_ms = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.estimated_cost = 0.0
        self.status = "success"
        self.error_message = None
        self.request_id = str(uuid.uuid4())


class GroqProvider:
    """Groq API wrapper with structured output support and usage tracking."""

    # Cost per million tokens (approximate for Groq models)
    COST_PER_M = {
        "qwen/qwen3.8-27b": {"input": 0.05, "output": 0.08},
        "openai/gpt-oss-120b": {"input": 0.24, "output": 0.24},
    }

    DEFAULT_MODEL = "qwen/qwen3.8-27b"
    ADVANCED_MODEL = "openai/gpt-oss-120b"

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise AIProviderError("GROQ_API_KEY not configured", retryable=False)
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        feature: str = "general",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> tuple[str, UsageStats]:
        """Generate text response from Groq."""
        model = model or self.DEFAULT_MODEL
        stats = UsageStats()
        stats.model = model
        stats.feature = feature

        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            stats.latency_ms = int((time.time() - start) * 1000)
            stats.input_tokens = response.usage.prompt_tokens if response.usage else 0
            stats.output_tokens = response.usage.completion_tokens if response.usage else 0
            stats.estimated_cost = self._estimate_cost(model, stats.input_tokens, stats.output_tokens)

            content = response.choices[0].message.content or ""
            return content, stats

        except RateLimitError as e:
            stats.status = "error"
            stats.error_message = "Rate limited by Groq"
            stats.latency_ms = int((time.time() - start) * 1000)
            raise AIProviderError("AI service is temporarily busy. Please try again in a moment.", retryable=True)
        except APITimeoutError:
            stats.status = "timeout"
            stats.error_message = "Groq API timeout"
            stats.latency_ms = int((time.time() - start) * 1000)
            raise AIProviderError("AI service timed out. Please try again.", retryable=True)
        except APIError as e:
            stats.status = "error"
            stats.error_message = str(e)
            stats.latency_ms = int((time.time() - start) * 1000)
            raise AIProviderError(f"AI service error: {str(e)}", retryable=False)
        except Exception as e:
            stats.status = "error"
            stats.error_message = str(e)
            stats.latency_ms = int((time.time() - start) * 1000)
            logger.error(f"Unexpected AI error: {e}")
            raise AIProviderError("An unexpected error occurred with the AI service.", retryable=False)

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        feature: str = "general",
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> tuple[dict, UsageStats]:
        """Generate structured JSON output from Groq, parsed and validated."""
        model = model or self.ADVANCED_MODEL
        json_system = system_prompt + "\n\nIMPORTANT: You MUST respond with ONLY valid JSON. No markdown, no code fences, no extra text."

        text, stats = await self.generate_text(
            system_prompt=json_system,
            user_prompt=user_prompt,
            feature=feature,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Parse JSON — strip common wrapping
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            return parsed, stats
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI JSON output: {e}\nRaw: {text[:500]}")
            raise AIProviderError(f"AI returned invalid structured output", retryable=True)

    async def generate_with_messages(
        self,
        messages: list[dict],
        feature: str = "tutor",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> tuple[str, UsageStats]:
        """Generate with full message list (for conversation)."""
        model = model or self.DEFAULT_MODEL
        stats = UsageStats()
        stats.model = model
        stats.feature = feature

        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            stats.latency_ms = int((time.time() - start) * 1000)
            stats.input_tokens = response.usage.prompt_tokens if response.usage else 0
            stats.output_tokens = response.usage.completion_tokens if response.usage else 0
            stats.estimated_cost = self._estimate_cost(model, stats.input_tokens, stats.output_tokens)

            return response.choices[0].message.content or "", stats

        except (RateLimitError, APITimeoutError, APIError) as e:
            stats.status = "error"
            stats.latency_ms = int((time.time() - start) * 1000)
            raise AIProviderError(str(e), retryable=isinstance(e, (RateLimitError, APITimeoutError)))

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        costs = self.COST_PER_M.get(model, {"input": 0.1, "output": 0.1})
        return round(
            (input_tokens / 1_000_000) * costs["input"] +
            (output_tokens / 1_000_000) * costs["output"],
            6
        )


# Singleton
_provider: Optional[GroqProvider] = None


def get_ai_provider() -> GroqProvider:
    global _provider
    if _provider is None:
        _provider = GroqProvider()
    return _provider


async def log_ai_usage(db, stats: UsageStats, user_id=None, project_id=None):
    """Persist AI usage to the database."""
    from app.models.models import AIUsageLog
    log = AIUsageLog(
        user_id=user_id,
        project_id=project_id,
        feature=stats.feature,
        model=stats.model,
        latency_ms=stats.latency_ms,
        input_tokens=stats.input_tokens,
        output_tokens=stats.output_tokens,
        estimated_cost=stats.estimated_cost,
        status=stats.status,
        error_message=stats.error_message,
        request_id=stats.request_id,
    )
    db.add(log)
