import streamlit as st
import requests
import time

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentFlow",
    page_icon="🤖",
    layout="wide"
)

API = "http://localhost:8000"

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    .agent-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #334155;
    }
    .agent-running { border-left: 4px solid #f59e0b; }
    .agent-done { border-left: 4px solid #10b981; }
    .agent-waiting { border-left: 4px solid #334155; }
    .task-badge {
        background: #1e40af;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 12px;
        color: #93c5fd;
    }
    .status-pill {
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "history" not in st.session_state:
    st.session_state.history = []
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "polling" not in st.session_state:
    st.session_state.polling = False

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("# 🤖 AgentFlow v2.0")
st.markdown("*Distributed Multi-Agent Orchestrator — Redis Queue + AsyncIO + LangGraph*")
st.divider()

# ── Layout ─────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2])

# ── Agents Definition ──────────────────────────────────────────────────────
agents = [
    {"name": "🧭 Planner Agent", "desc": "Breaks task into subtasks"},
    {"name": "🔍 Researcher Agent", "desc": "Parallel asyncio research"},
    {"name": "⚙️ Executor Agent", "desc": "Processes & structures data"},
    {"name": "📝 Synthesizer Agent", "desc": "Writes final report"},
]

# ════════════════════════════════════════════════
# LEFT — Input + Agent Status
# ════════════════════════════════════════════════
with left:
    st.markdown("### 📋 Enter Your Task")

    examples = [
        "Research top 5 AI companies and compare salaries",
        "Analyze the best programming languages to learn in 2025",
        "Compare AWS vs Google Cloud vs Azure for startups",
        "Research the best backend frameworks for high scale systems"
    ]

    st.markdown("**Try these examples:**")
    for example in examples:
        if st.button(example, use_container_width=True, key=example):
            st.session_state.selected_task = example

    st.markdown("<br>", unsafe_allow_html=True)

    task_input = st.text_area(
        "Or type your own task:",
        value=st.session_state.get("selected_task", ""),
        height=100,
        placeholder="e.g. Research the top AI frameworks..."
    )

    run_button = st.button("🚀 Run AgentFlow", use_container_width=True, type="primary")

    # ── Agent Pipeline Status ──────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔄 Agent Pipeline")

    agent_placeholders = []
    for agent in agents:
        placeholder = st.empty()
        agent_placeholders.append(placeholder)

        # ✅ FIX: Show correct status based on session state
        if st.session_state.result:
            placeholder.markdown(f"""
            <div class="agent-card agent-done">
                <b>{agent['name']}</b><br>
                <small style="color:#64748b">{agent['desc']}</small><br>
                <small style="color:#10b981">✅ Complete</small>
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.polling:
            placeholder.markdown(f"""
            <div class="agent-card agent-running">
                <b>{agent['name']}</b><br>
                <small style="color:#64748b">{agent['desc']}</small><br>
                <small style="color:#f59e0b">⚡ Running...</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            placeholder.markdown(f"""
            <div class="agent-card agent-waiting">
                <b>{agent['name']}</b><br>
                <small style="color:#64748b">{agent['desc']}</small><br>
                <small style="color:#475569">⏳ Waiting...</small>
            </div>
            """, unsafe_allow_html=True)

    # ── Architecture Info ──────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    <div style="background:#1e293b; border-radius:10px; padding:12px; font-size:12px; color:#94a3b8">
        <b style="color:#10b981">Redis Queue</b> → API returns job_id instantly<br>
        <b style="color:#6366f1">Celery Worker</b> → Processes task in background<br>
        <b style="color:#f59e0b">AsyncIO</b> → Researcher runs subtasks in parallel<br>
        <b style="color:#ec4899">LangGraph</b> → Orchestrates agent pipeline
    </div>
    """, unsafe_allow_html=True)

    # ── Task History ───────────────────────────────────────────────────────
    if st.session_state.history:
        st.divider()
        st.markdown("### 📚 History")
        for h in st.session_state.history[-3:]:
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:8px; padding:8px 12px; margin:4px 0; font-size:12px; color:#94a3b8">
                ✅ {h[:55]}...
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# RIGHT — Results
# ════════════════════════════════════════════════
with right:
    st.markdown("### 📊 Results")

    results_placeholder = st.empty()

    if not st.session_state.result and not st.session_state.polling:
        results_placeholder.markdown("""
        <div style="background:#1e293b; border-radius:12px; padding:40px; text-align:center; border:1px dashed #334155; margin-top:20px">
            <div style="font-size:48px">🤖</div>
            <div style="color:#475569; margin-top:12px">Enter a task and click Run AgentFlow</div>
            <div style="color:#334155; font-size:12px; margin-top:8px">
                API returns job_id instantly → Redis queues task → Worker processes → You get results
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Submit Task ────────────────────────────────────────────────────────
    if run_button and task_input.strip():
        st.session_state.result = None
        st.session_state.job_id = None
        st.session_state.polling = False

        try:
            # POST to /run — returns job_id INSTANTLY
            response = requests.post(
                f"{API}/run",
                json={"task": task_input},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.job_id = data["job_id"]
                st.session_state.polling = True
                st.session_state.history.append(task_input)

                results_placeholder.markdown(f"""
                <div style="background:#1e293b; border-radius:12px; padding:24px; border:1px solid #334155; text-align:center">
                    <div style="font-size:32px">⚡</div>
                    <div style="color:#10b981; font-size:16px; margin-top:8px">Task Queued in Redis!</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:8px">Job ID: {data['job_id'][:16]}...</div>
                    <div style="color:#475569; font-size:12px; margin-top:4px">Worker is processing in background...</div>
                </div>
                """, unsafe_allow_html=True)

                st.rerun()

            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

        except Exception as e:
            st.error(f"❌ Cannot connect to backend!\n{str(e)}")

    # ── Poll for Results ───────────────────────────────────────────────────
    if st.session_state.polling and st.session_state.job_id:
        with right:
            progress_bar = st.progress(0)
            status_text = st.empty()

        poll_count = 0
        max_polls = 60

        while st.session_state.polling and poll_count < max_polls:
            try:
                status_response = requests.get(
                    f"{API}/status/{st.session_state.job_id}",
                    timeout=5
                )
                status_data = status_response.json()
                job_status = status_data.get("status", "pending")

                poll_count += 1
                progress = min(int((poll_count / max_polls) * 90), 90)
                progress_bar.progress(progress)

                if job_status == "pending":
                    status_text.markdown("⏳ Task waiting in Redis queue...")

                elif job_status == "started":
                    status_text.markdown("⚡ Worker picked up task — agents running...")

                elif job_status == "success":
                    progress_bar.progress(100)
                    status_text.markdown("✅ AgentFlow Complete!")
                    st.session_state.result = status_data.get("result", {})
                    st.session_state.polling = False
                    st.rerun()

                elif job_status == "failure":
                    st.error(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
                    st.session_state.polling = False
                    break

                time.sleep(2)

            except Exception as e:
                st.error(f"❌ Polling error: {str(e)}")
                st.session_state.polling = False
                break

    # ── Display Results ────────────────────────────────────────────────────
    if st.session_state.result:
        data = st.session_state.result

        # Subtasks
        with st.expander("🧭 Planner Output — Subtasks", expanded=False):
            for i, subtask in enumerate(data.get("subtasks", [])):
                st.markdown(f"""
                <div class="agent-card">
                    <span class="task-badge">Subtask {i+1}</span>
                    <span style="margin-left:10px">{subtask}</span>
                </div>
                """, unsafe_allow_html=True)

        # Research Results
        with st.expander("🔍 Researcher Output — Parallel Findings", expanded=False):
            for result in data.get("research_results", []):
                st.markdown(f"**{result.get('subtask', '')}**")
                st.markdown(result.get('findings', ''))
                for point in result.get('key_points', []):
                    st.markdown(f"• {point}")
                st.divider()

        # Key Insights
        processed = data.get("processed_data", {})
        if processed.get("key_insights"):
            with st.expander("⚙️ Executor Output — Insights", expanded=False):
                for insight in processed.get("key_insights", []):
                    st.markdown(f"✅ {insight}")
                for rec in processed.get("recommendations", []):
                    st.markdown(f"💡 {rec}")
                st.markdown(f"**Confidence:** `{processed.get('confidence_score', 'N/A')}`")

        # Final Report
        final = data.get("final_report", {})
        if final.get("report"):
            st.markdown("### 📝 Final Report")
            st.markdown(
                f'<div style="background:#1e293b; border-radius:12px; padding:24px; border:1px solid #334155">{final["report"]}</div>',
                unsafe_allow_html=True
            )

        # Clear button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.result = None
            st.session_state.job_id = None
            st.session_state.polling = False
            st.rerun()