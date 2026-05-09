import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class ExecutorAgent:
    """
    Executor Agent — The Data Processor of AgentFlow.

    Takes all raw research results from the Researcher Agent
    and processes, structures, and analyzes them into clean
    structured data ready for the Synthesizer Agent.

    Think of it as the data engineer of the team — it cleans,
    organizes, and extracts insights from raw research.

    Example:
        Input:  List of raw research results from 5 companies
        Output: {
            "processed_results": [...],
            "comparisons": {...},
            "rankings": [...],
            "key_insights": [...]
        }
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def execute(self, task: str, research_results: list[dict]) -> dict:
        """
        Processes all research results and extracts structured insights.
        Returns a clean, organized analysis ready for the Synthesizer.
        """
        print(f"⚙️ Executor Agent: Processing {len(research_results)} research results...")

        # Format research results for the LLM
        research_text = ""
        for i, result in enumerate(research_results):
            research_text += f"\n--- Research {i+1}: {result.get('subtask', '')} ---\n"
            research_text += f"Findings: {result.get('findings', '')}\n"
            key_points = result.get('key_points', [])
            if key_points:
                research_text += "Key Points:\n"
                for point in key_points:
                    research_text += f"  • {point}\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a data analysis expert. Process the provided research results "
                        "and extract structured insights. "
                        "Respond ONLY with a valid JSON object containing: "
                        "- processed_results: array of cleaned result objects with subtask and summary "
                        "- key_insights: array of 5 most important findings as strings "
                        "- comparisons: object with any relevant comparisons found "
                        "- recommendations: array of 3 actionable recommendation strings "
                        "- confidence_score: overall confidence as a percentage string like '85%' "
                        "No explanation, no markdown, just valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Original task: {task}\n\n"
                        f"Research Results to process:\n{research_text}"
                    )
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        try:
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            print(f"⚙️ Executor Agent: Processing complete!")
            return result
        except json.JSONDecodeError:
            print(f"⚙️ Executor Agent: Processing complete (fallback)!")
            return {
                "processed_results": [{"subtask": r.get("subtask", ""), "summary": r.get("findings", "")[:200]} for r in research_results],
                "key_insights": [r.get("findings", "")[:100] for r in research_results[:5]],
                "comparisons": {},
                "recommendations": ["Review the research findings carefully"],
                "confidence_score": "70%"
            }