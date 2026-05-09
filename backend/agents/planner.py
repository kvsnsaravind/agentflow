import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class PlannerAgent:
    """
    Planner Agent — The Project Manager of AgentFlow.

    Receives a complex user task and breaks it down into
    a list of clear, actionable subtasks that other agents
    can execute independently.

    Example:
        Input:  "Research top 5 AI companies and compare salaries"
        Output: [
            "Search for top 5 AI companies in 2025",
            "Find average engineer salary at Google",
            "Find average engineer salary at OpenAI",
            ...
        ]
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def plan(self, task: str) -> list[str]:
        """
        Takes a complex task and returns a list of subtasks.
        Each subtask is a clear, self-contained research question.
        """
        print(f"🧭 Planner Agent: Breaking down task...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a task planning expert. Your job is to break down "
                        "complex tasks into 3-5 clear, specific, self-contained subtasks. "
                        "Each subtask should be something a researcher can independently search for. "
                        "Respond ONLY with a valid JSON array of strings. "
                        "Example: [\"subtask 1\", \"subtask 2\", \"subtask 3\"] "
                        "No explanation, no markdown, just the JSON array."
                    )
                },
                {
                    "role": "user",
                    "content": f"Break this task into subtasks: {task}"
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        # Safely parse JSON response
        try:
            # Remove markdown backticks if present
            raw = raw.replace("```json", "").replace("```", "").strip()
            subtasks = json.loads(raw)
            if isinstance(subtasks, list):
                print(f"🧭 Planner Agent: Created {len(subtasks)} subtasks")
                return subtasks
        except json.JSONDecodeError:
            pass

        # Fallback: split by newlines if JSON fails
        subtasks = [line.strip("- •").strip()
                    for line in raw.split("\n")
                    if line.strip()]
        print(f"🧭 Planner Agent: Created {len(subtasks)} subtasks (fallback)")
        return subtasks[:5]  # Max 5 subtasks