"""Gemini LLM scorer — structured output, retry, circuit breaker (D9, ADR-0011)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from events.models import EventScoreResult, NormalizedEvent
from events.scoring.base import EventScorer
from events.scoring.prompt import build_user_prompt, load_system_prompt

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MAX_RETRIES = 3
BACKOFF_BASE = 0.5
TIMEOUT_SECONDS = 30
CIRCUIT_BREAKER_THRESHOLD = 3

try:
    import google.genai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]


class EventScoreSchema(BaseModel):
    """Pydantic model for one scored event in the Gemini response."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    impact_score: int = Field(ge=0, le=100)
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    affected_nights: list[date]
    rationale: str = Field(max_length=240)


class EventScoresResponse(BaseModel):
    """Top-level Gemini response wrapper."""

    model_config = ConfigDict(extra="forbid")

    scores: list[EventScoreSchema]


class GeminiScorer(EventScorer):
    """Score events using Google Gemini with structured output."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        prompt_version: str = "event-impact-v1",
        budget_check: Any = None,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._api_key = api_key
        self._model = model
        self._prompt_version = prompt_version
        self._budget_check = budget_check
        self._consecutive_failures = 0
        self._system_prompt: str | None = None

    def _get_system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = load_system_prompt(self._prompt_version)
        return self._system_prompt

    @property
    def is_circuit_open(self) -> bool:
        return self._consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD

    async def score(self, events: list[NormalizedEvent]) -> list[EventScoreResult]:
        if not events:
            return []

        results: list[EventScoreResult] = []
        for i in range(0, len(events), BATCH_SIZE):
            batch = events[i : i + BATCH_SIZE]

            if self.is_circuit_open:
                logger.warning("Gemini circuit breaker open — skipping batch")
                break

            if self._budget_check and not self._budget_check():
                logger.warning("Gemini daily budget exhausted — skipping batch")
                break

            batch_results = await self._score_batch(batch)
            if batch_results is not None:
                results.extend(batch_results)
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1

        return results

    async def _score_batch(
        self,
        events: list[NormalizedEvent],
    ) -> list[EventScoreResult] | None:
        if genai is None:
            logger.error("google-genai SDK not installed")
            return None

        client = genai.Client(api_key=self._api_key)
        system_prompt = self._get_system_prompt()
        user_prompt = build_user_prompt(events)

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=self._model,
                        contents=user_prompt,
                        config=genai.types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.1,
                            response_mime_type="application/json",
                            response_schema=EventScoresResponse,
                        ),
                    ),
                    timeout=TIMEOUT_SECONDS,
                )

                raw_text = response.text
                raw_json: dict[str, Any] = {}
                with contextlib.suppress(Exception):
                    raw_json = json.loads(raw_text)

                try:
                    parsed = EventScoresResponse.model_validate_json(raw_text)
                except Exception:
                    if attempt < MAX_RETRIES:
                        logger.warning("Gemini response validation failed — retry %d", attempt + 1)
                        user_prompt = (
                            f"The previous response was invalid JSON. "
                            f"Fix it and return valid JSON conforming to the schema.\n\n"
                            f"Original response:\n{raw_text}\n\n"
                            f"Original request:\n{build_user_prompt(events)}"
                        )
                        await asyncio.sleep(BACKOFF_BASE * (2**attempt))
                        continue
                    logger.error("Gemini response validation failed after retries")
                    return None

                results: list[EventScoreResult] = []
                for score_item in parsed.scores:
                    results.append(
                        EventScoreResult(
                            event_external_id=score_item.event_id,
                            impact_score=score_item.impact_score,
                            confidence=score_item.confidence,
                            affected_nights=score_item.affected_nights,
                            rationale=score_item.rationale,
                            is_fallback=False,
                            response_raw=raw_json,
                        )
                    )

                return results

            except TimeoutError:
                logger.warning("Gemini timeout on attempt %d", attempt + 1)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(BACKOFF_BASE * (2**attempt))
                    continue
                return None
            except Exception:
                logger.exception("Gemini scoring error on attempt %d", attempt + 1)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(BACKOFF_BASE * (2**attempt))
                    continue
                return None

        return None
