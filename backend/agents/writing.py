from openai import OpenAI
from agents.base import BaseAgent
from models import TaskCategory, Subtask, SubtaskResult
import config


class WritingAgent(BaseAgent):
    category = TaskCategory.WRITING
    system_prompt = config.WRITING_SYSTEM_PROMPT

    def __init__(self, client: OpenAI) -> None:
        super().__init__(client)

    def execute(self, subtask: Subtask, context: str) -> SubtaskResult:
        user_message = (
            f"Task: {subtask.description}\n\n"
            f"Context: {context}\n\n"
            f"Deliverable required: {subtask.expected_output}\n\n"
            "Write high-quality, publish-ready content. "
            "Include a strong hook, structured body, and actionable conclusion."
        )
        output, tokens = self._call_tokenrouter(user_message)
        return SubtaskResult(subtask_id=subtask.id, agent=self.category, output=output, tokens_used=tokens)
