import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SynthesizerAgent:
    """
    Synthesizer Agent — The Report Writer of AgentFlow.

    Takes all processed data from the Executor Agent and
    writes a comprehensive, human-readable final report.

    This is the last agent in the pipeline — it combines
    everything into a polished, actionable response for the user.

    Example:
        Input:  Processed analysis from Executor Agent
        Output: A clean, well-structured report with:
                - Executive summary
                - Key findings
                - Recommendations
                - Conclusion
    """

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def synthesize(self, task: str, processed_data: dict) -> dict:
        """
        Takes processed data and writes a comprehensive final report.
        Returns a structured report with summary, findings, and recommendations.
        """
        print(f"📝 Synthesizer Agent: Writing final report...")

        # Format processed data for the LLM
        insights = processed_data.get("key_insights", [])
        recommendations = processed_data.get("recommendations", [])
        comparisons = processed_data.get("comparisons", {})
        confidence = processed_data.get("confidence_score", "N/A")
        processed_results = processed_data.get("processed_results", [])

        data_text = f"""
Key Insights:
{chr(10).join(f'• {i}' for i in insights)}

Recommendations:
{chr(10).join(f'• {r}' for r in recommendations)}

Comparisons:
{str(comparisons)}

Confidence Score: {confidence}

Detailed Results:
{chr(10).join(f'- {r.get("subtask", "")}: {r.get("summary", "")}' for r in processed_results)}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert report writer. Take the processed research data "
                        "and write a comprehensive, well-structured, human-readable report. "
                        "The report should be clear, insightful, and actionable. "
                        "Structure it with these sections using markdown: "
                        "## Executive Summary, ## Key Findings, ## Detailed Analysis, "
                        "## Recommendations, ## Conclusion. "
                        "Be specific, reference actual data points, and make it genuinely useful."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Original task: {task}\n\n"
                        f"Processed Data:\n{data_text}\n\n"
                        f"Write a comprehensive final report."
                    )
                }
            ]
        )

        report = response.choices[0].message.content.strip()
        print(f"📝 Synthesizer Agent: Report complete!")

        return {
            "report": report,
            "key_insights": insights,
            "recommendations": recommendations,
            "confidence_score": confidence,
            "task": task
        }