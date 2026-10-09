import json
from typing import TypeVar

from openai import APIError, APITimeoutError, OpenAI
from pydantic import BaseModel, ValidationError

from backend.app.core.config import settings

Output = TypeVar("Output", bound=BaseModel)


class LLMError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def encoded_size(value: object) -> int:
    # UTF-8 byte count is a conservative upper bound for text token budgeting.
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


class OpenAIProvider:
    def __init__(self):
        key = settings.groq_api_key

        if key is None or not key.get_secret_value().strip():
            raise LLMError(
                "Configure GROQ_API_KEY to run Day 9 evaluation.",
                503,
            )

        self.client = OpenAI(
            api_key=key.get_secret_value(),
            base_url=settings.groq_base_url,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )

    def close(self) -> None:
        self.client.close()

    def structured(
        self,
        *,
        model: str,
        instructions: str,
        payload: dict,
        schema: type[Output],
    ) -> Output:
        try:
            response = self.client.responses.parse(
                model=model,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=schema,
                max_output_tokens=4096,
            )
        except APITimeoutError as error:
            raise LLMError(
                "The LLM provider timed out.",
                504,
            ) from error
        except APIError as error:
            raise LLMError(
                "The LLM provider could not complete the request."
            ) from error
        except (ValidationError, ValueError) as error:
            raise LLMError(
                "The LLM returned invalid structured output."
            ) from error

        if response.status != "completed":
            raise LLMError("The LLM response was incomplete.")

        if response.output_parsed is None:
            raise LLMError(
                "The LLM refused or returned no structured output."
            )

        return response.output_parsed