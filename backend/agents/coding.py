from openai import OpenAI
from agents.base import BaseAgent
from models import TaskCategory, Subtask, SubtaskResult
import config


class CodingAgent(BaseAgent):
    category = TaskCategory.CODING
    system_prompt = config.CODING_SYSTEM_PROMPT

    def __init__(self, client: OpenAI) -> None:
        super().__init__(client)

    def execute(self, subtask: Subtask, context: str) -> SubtaskResult:
        user_message = (
            f"Task: {subtask.description}\n\n"
            f"Context: {context}\n\n"
            f"Deliverable required: {subtask.expected_output}\n\n"
            "Provide working, production-quality code. "
            "Include: brief approach explanation, complete code in a fenced block, usage example, edge cases."
        )
        output, tokens = self._call_tokenrouter(user_message)
        return SubtaskResult(subtask_id=subtask.id, agent=self.category, output=output, tokens_used=tokens)
