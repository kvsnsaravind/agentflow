import os
import json
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()


class ResearcherAgent:
    """
    Researcher Agent — The Information Gatherer of AgentFlow.

    UPGRADED: Now uses asyncio + AsyncGroq to research ALL subtasks
    in PARALLEL simultaneously instead of one by one.

    Before (sequential):
        Subtask 1 → 8s → Subtask 2 → 8s → Subtask 3 → 8s = 24s total

    After (parallel):
        Subtask 1 → |
        Subtask 2 → | all run at same time = 8s total
        Subtask 3 → |

    This is the core scaling improvement — asyncio.gather() fires
    all LLM calls simultaneously and waits for all to complete.
    """

    def __init__(self):
        # AsyncGroq is the async version — supports await calls
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    async def research(self, subtask: str) -> dict:
        """
        Researches a single subtask asynchronously.
        Uses await so other subtasks can run while this one waits.
        """
        print(f"🔍 Researcher Agent: Starting '{subtask[:50]}...'")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert researcher. Research the given topic thoroughly "
                        "and provide detailed, accurate findings. "
                        "Respond ONLY with a valid JSON object containing: "
                        "- findings: detailed paragraph of what you found "
                        "- key_points: array of 3-5 bullet point strings "
                        "- confidence: 'high', 'medium', or 'low' "
                        "No explanation, no markdown, just valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": f"Research this topic thoroughly: {subtask}"
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        try:
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            result["subtask"] = subtask
            print(f"✅ Researcher Agent: Done '{subtask[:40]}...'")
            return result
        except json.JSONDecodeError:
            print(f"✅ Researcher Agent: Done (fallback) '{subtask[:40]}...'")
            return {
                "subtask": subtask,
                "findings": raw,
                "key_points": [raw[:100]],
                "confidence": "medium"
            }

    async def research_all(self, subtasks: list[str]) -> list[dict]:
        """
        ⚡ THE KEY METHOD — Runs all subtasks in PARALLEL.

        asyncio.gather() is the magic here:
        - Creates a coroutine for each subtask
        - Fires ALL of them at the same time
        - Waits until ALL complete
        - Returns all results together

        This is what cuts research time from 40s → 10s
        """
        print(f"\n⚡ Researcher Agent: Launching {len(subtasks)} subtasks IN PARALLEL...")
        print(f"   Subtasks: {[s[:30] for s in subtasks]}\n")

        # Create async tasks for ALL subtasks simultaneously
        tasks = [self.research(subtask) for subtask in subtasks]

        # Fire all tasks at the same time and wait for all to finish
        results = await asyncio.gather(*tasks)

        print(f"\n✅ Researcher Agent: All {len(results)} subtasks complete!")
        return list(results)