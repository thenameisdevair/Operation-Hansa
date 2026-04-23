from openai import OpenAI
from agents.base import BaseAgent
from models import TaskCategory, Subtask, SubtaskResult
import config


class MarketingAgent(BaseAgent):
    category = TaskCategory.MARKETING
    system_prompt = config.MARKETING_SYSTEM_PROMPT

    def __init__(self, client: OpenAI) -> None:
        super().__init__(client)

    def execute(self, subtask: Subtask, context: str) -> SubtaskResult:
        user_message = (
            f"Task: {subtask.description}\n\n"
            f"Context: {context}\n\n"
            f"Deliverable required: {subtask.expected_output}\n\n"
            "Develop a strategic marketing plan with: target audience, core message, "
            "channel strategy, content direction, and measurable success metrics."
        )
        output, tokens = self._call_tokenrouter(user_message)
        return SubtaskResult(subtask_id=subtask.id, agent=self.category, output=output, tokens_used=tokens)
