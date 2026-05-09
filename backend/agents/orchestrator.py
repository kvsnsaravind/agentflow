import asyncio
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.executor import ExecutorAgent
from agents.synthesizer import SynthesizerAgent


# ── LangGraph State ────────────────────────────────────────────────────────
class AgentState(TypedDict):
    """
    Shared state that flows through all agents in the graph.
    Each agent reads from and writes to this state.
    """
    task: str
    subtasks: List[str]
    research_results: List[Dict]
    processed_data: Dict
    final_report: Dict
    current_agent: str
    status: str


# ── Orchestrator ───────────────────────────────────────────────────────────
class AgentOrchestrator:
    """
    AgentFlow Orchestrator — Updated with Async Researcher.

    Flow:
    Planner → Researcher (PARALLEL asyncio) → Executor → Synthesizer

    The key upgrade: Researcher now uses asyncio.gather() to
    research all subtasks simultaneously instead of sequentially.
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.executor = ExecutorAgent()
        self.synthesizer = SynthesizerAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph agent flow."""
        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self._planner_node)
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("synthesizer", self._synthesizer_node)

        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "executor")
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    # ── Node 1: Planner ────────────────────────────────────────────────────
    def _planner_node(self, state: AgentState) -> AgentState:
        """Breaks the task into subtasks."""
        print("\n🧭 Planner Agent: Starting...")
        state["current_agent"] = "Planner Agent"
        state["status"] = "planning"
        subtasks = self.planner.plan(state["task"])
        state["subtasks"] = subtasks
        print(f"🧭 Planner Agent: Created {len(subtasks)} subtasks\n")
        return state

    # ── Node 2: Researcher (ASYNC) ─────────────────────────────────────────
    def _researcher_node(self, state: AgentState) -> AgentState:
        """
        Runs all subtasks IN PARALLEL using asyncio.
        This is the key performance improvement.
        """
        print("\n⚡ Researcher Agent: Running subtasks in PARALLEL...")
        state["current_agent"] = "Researcher Agent"
        state["status"] = "researching"

        # Run async research_all inside sync LangGraph node
        # asyncio.run() creates an event loop and runs the coroutine
        results = asyncio.run(
            self.researcher.research_all(state["subtasks"])
        )

        state["research_results"] = results
        return state

    # ── Node 3: Executor ───────────────────────────────────────────────────
    def _executor_node(self, state: AgentState) -> AgentState:
        """Processes and structures all research results."""
        print("\n⚙️ Executor Agent: Processing results...")
        state["current_agent"] = "Executor Agent"
        state["status"] = "processing"
        processed = self.executor.execute(
            state["task"],
            state["research_results"]
        )
        state["processed_data"] = processed
        return state

    # ── Node 4: Synthesizer ────────────────────────────────────────────────
    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Writes the final report."""
        print("\n📝 Synthesizer Agent: Writing report...")
        state["current_agent"] = "Synthesizer Agent"
        state["status"] = "synthesizing"
        report = self.synthesizer.synthesize(
            state["task"],
            state["processed_data"]
        )
        state["final_report"] = report
        state["status"] = "complete"
        return state

    def run(self, task: str) -> Dict:
        """
        Main entry point. Runs the full agent pipeline.
        Researcher subtasks now execute in parallel.
        """
        print(f"\n🚀 AgentFlow Starting...")
        print(f"📋 Task: {task}\n")

        initial_state: AgentState = {
            "task": task,
            "subtasks": [],
            "research_results": [],
            "processed_data": {},
            "final_report": {},
            "current_agent": "",
            "status": "starting"
        }

        final_state = self.graph.invoke(initial_state)

        print(f"\n✅ AgentFlow Complete!")

        return {
            "task": task,
            "subtasks": final_state["subtasks"],
            "research_results": final_state["research_results"],
            "processed_data": final_state["processed_data"],
            "final_report": final_state["final_report"],
            "status": final_state["status"]
        }