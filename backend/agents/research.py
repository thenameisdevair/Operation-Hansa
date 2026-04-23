from openai import OpenAI
from agents.base import BaseAgent
from models import TaskCategory, Subtask, SubtaskResult
import config


class ResearchAgent(BaseAgent):
    category = TaskCategory.RESEARCH
    system_prompt = config.RESEARCH_SYSTEM_PROMPT

    def __init__(self, client: OpenAI) -> None:
        super().__init__(client)

    def execute(self, subtask: Subtask, context: str) -> SubtaskResult:
        user_message = (
            f"Task: {subtask.description}\n\n"
            f"Context: {context}\n\n"
            f"Deliverable required: {subtask.expected_output}\n\n"
            "Conduct thorough research. Cite sources. Flag low-confidence claims. "
            "Structure your output with: Summary, Key Findings, Data & Evidence, Sources, Gaps."
        )
        output, tokens = self._call_tokenrouter(user_message)
        return SubtaskResult(subtask_id=subtask.id, agent=self.category, output=output, tokens_used=tokens)
