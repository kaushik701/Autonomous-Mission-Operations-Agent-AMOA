"""
Provider abstraction for all LLM calls in AMOA.

Every agent call goes through structured_completion().
Agents never import anthropic, groq, or google.genai directly.
"""

import base64
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from google import genai
from google.genai import types as genai_types
from groq import AsyncGroq
from pydantic import BaseModel, ValidationError

from amoa.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

FAILURES_LOG = Path(__file__).parent / "eval" / "failures.jsonl"

# Failure categories
CATEGORY_SCHEMA_VIOLATION = "schema_violation"
CATEGORY_REFUSAL = "refusal"
CATEGORY_TIMEOUT = "timeout"
CATEGORY_RATE_LIMIT = "rate_limit"
CATEGORY_MALFORMED_JSON = "malformed_json"


def _log_failure(
    category: str,
    provider: str,
    model: str,
    raw_output: str,
    error: str,
    schema_name: str,
) -> None:
    """Append one failure record to eval/failures.jsonl."""
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "category": category,
        "provider": provider,
        "model": model,
        "schema": schema_name,
        "error": error,
        "raw_output": raw_output[:500],  # truncate — don't bloat the log
    }
    FAILURES_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FAILURES_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _parse_json_output(raw: str) -> dict:
    """
    Strip markdown fences and parse JSON.
    LLMs often wrap JSON in ```json ... ``` blocks.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1])
    return json.loads(cleaned)


async def structured_completion(
    system: str,
    user: str,
    schema: type[T],
    *,
    provider: str | None = None,
    image_b64: str | None = None,
    max_retries: int = 1,
) -> T:
    """
    Call an LLM and return a validated Pydantic model.

    Args:
        system: System prompt.
        user: User message.
        schema: Pydantic model class to validate against.
        provider: Override AMOA_LLM_PROVIDER for this call.
        max_retries: How many correction retries before giving up (default 1).

    Returns:
        Validated instance of schema.

    Raises:
        ValueError: If output cannot be parsed after retries.
    """
    resolved_provider = provider or settings.amoa_llm_provider
    schema_name = schema.__name__

    raw_output = ""
    last_error = ""

    for attempt in range(max_retries + 1):
        user_message = user if attempt == 0 else (
            f"{user}\n\n"
            f"Your previous response was invalid. Error: {last_error}\n"
            f"Return only valid JSON matching the schema. No markdown, no explanation."
        )

        try:
            raw_output = await _call_provider(
                resolved_provider, system, user_message, image_b64=image_b64
            )
        except Exception as e:
            category = CATEGORY_RATE_LIMIT if "429" in str(e) else CATEGORY_TIMEOUT
            _log_failure(category, resolved_provider, _model_for(resolved_provider),
                         "", str(e), schema_name)
            raise

        # Attempt parse
        # ValidationError before ValueError: Pydantic v2 ValidationError is a
        # subclass of ValueError, so order matters — specific first.
        try:
            data = _parse_json_output(raw_output)
            return schema.model_validate(data)
        except ValidationError as e:
            last_error = f"Schema validation error: {e.errors()}"
            category = CATEGORY_SCHEMA_VIOLATION
        except (json.JSONDecodeError, ValueError) as e:
            last_error = f"JSON parse error: {e}"
            category = CATEGORY_MALFORMED_JSON

        logger.warning(
            "Attempt %d/%d failed for %s: %s",
            attempt + 1, max_retries + 1, schema_name, last_error
        )

    # All retries exhausted
    _log_failure(
        category, resolved_provider, _model_for(resolved_provider),
        raw_output, last_error, schema_name
    )
    raise ValueError(
        f"structured_completion failed for {schema_name} after "
        f"{max_retries + 1} attempts. Last error: {last_error}"
    )


def _model_for(provider: str) -> str:
    models = {
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-2.5-flash",
        "gemini-vision": "gemini-2.5-flash",
    }
    if provider not in models:
        raise ValueError(f"Unknown provider: {provider!r}. "
                         f"Valid options: {list(models)}")
    return models[provider]


async def _call_provider(
    provider: str, system: str, user: str, *, image_b64: str | None = None
) -> str:
    """Route to the correct SDK and return raw string output."""
    if provider == "groq":
        client = AsyncGroq(api_key=settings.groq_api_key)
        response = await client.chat.completions.create(
            model=_model_for(provider),
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    elif provider == "gemini":
        client = genai.Client(api_key=settings.google_api_key)
        response = await client.aio.models.generate_content(
            model=_model_for(provider),
            contents=user,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=1024,
            ),
        )
        return response.text

    elif provider == "gemini-vision":
        if image_b64 is None:
            raise ValueError("gemini-vision requires image_b64")
        client = genai.Client(api_key=settings.google_api_key)
        contents = [
            genai_types.Part(text=user),
            genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type="image/jpeg",
                    data=base64.b64decode(image_b64),
                )
            ),
        ]
        response = await client.aio.models.generate_content(
            model=_model_for(provider),
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=1024,
            ),
        )
        return response.text

    else:
        raise ValueError(f"Unknown provider: {provider!r}")