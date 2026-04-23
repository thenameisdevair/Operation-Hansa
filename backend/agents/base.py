from __future__ import annotations
from abc import ABC, abstractmethod
from openai import OpenAI
from models import TaskCategory, Subtask, SubtaskResult
import config


class AgentError(Exception):
    pass


class BaseAgent(ABC):
    category: TaskCategory
    system_prompt: str

    def __init__(self, client: OpenAI) -> None:
        self.client = client

    @abstractmethod
    def execute(self, subtask: Subtask, context: str) -> SubtaskResult:
        ...

    def _call_tokenrouter(self, user_message: str) -> tuple[str, int]:
        try:
            response = self.client.chat.completions.create(
                model=config.TOKENROUTER_MODEL,
                max_tokens=config.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            content = response.choices[0].message.content or ""
            tokens = (
                response.usage.total_tokens if response.usage else len(content) // 4
            )
            return content, tokens
        except Exception as exc:
            raise AgentError(
                f"{self.__class__.__name__} failed on subtask: {exc}"
            ) from exc
