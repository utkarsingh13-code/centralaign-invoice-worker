from __future__ import annotations

import json
import uuid
from pathlib import Path

import streamlit as st
from langgraph.types import Command

from worker import build_graph, db_connect, init_db

st.set_page_config(page_title="CentrAlign | Autonomous Invoice Worker", page_icon="🧾", layout="wide")

@st.cache_resource
def get_graph():
    return build_graph()

graph = get_graph()
init_db()

st.title("🧾 Autonomous Invoice Worker")
st.caption("A narrow, working proof of concept for the CentrAlign AI Engineering Internship.")
st.info("Demo environment only: invoice files are local samples and the internal company system is a local SQLite database. A human must approve every write.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "run_state" not in st.session_state:
    st.session_state.run_state = None
if "pending" not in st.session_state:
    st.session_state.pending = False

with st.sidebar:
    st.subheader("Available tools")
    st.markdown("- Read local invoice files (`.txt` / `.pdf`)\n- Extract and validate fields\n- Ask for human approval\n- Write to SQLite company system\n- Re-read and verify the saved record")
    st.caption("Optional LLM: configure OPENAI_API_KEY in `.env`. Without it, a deterministic local parser keeps the demo runnable.")
    if st.button("Start a new task / thread"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.run_state = None
        st.session_state.pending = False
        st.rerun()

task = st.text_input(
    "What should the AI worker do?",
    value="Find the latest invoice from ACME OFFICE SUPPLIES, extract the amount and due date, add it to the company system, and confirm when done.",
    help="Try a vendor from the sample invoice folder, e.g. ACME OFFICE SUPPLIES or NORTHSTAR CLOUD SERVICES."
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Run worker", type="primary", disabled=st.session_state.pending):
        st.session_state.thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        with st.spinner("Worker is planning and executing..."):
            state = graph.invoke(
                {"task": task, "retry_count": 0, "errors": [], "messages": [], "evidence": []},
                config=config,
            )
        st.session_state.run_state = state
        st.session_state.pending = bool(graph.get_state(config).next)
        st.rerun()

state = st.session_state.run_state
config = {"configurable": {"thread_id": st.session_state.thread_id}}

if state:
    st.subheader("Execution status")
    status = state.get("status", "running")
    st.write(f"**Status:** `{status}`")
    if state.get("messages"):
        with st.expander("Agent trace", expanded=True):
            for i, message in enumerate(state["messages"], 1):
                st.write(f"{i}. {message}")
    if state.get("invoice"):
        st.subheader("Extracted invoice fields")
        st.json(state["invoice"])
    if state.get("errors"):
        st.error("\n".join(state["errors"]))

    snapshot = graph.get_state(config)
    if snapshot.next and st.session_state.pending:
        st.warning("The worker is paused at a human approval checkpoint. No database write has happened yet.")
        invoice = (snapshot.values or {}).get("invoice", {})
        st.write("Review the exact values that will be written:")
        st.json(invoice)
        a, b = st.columns(2)
        with a:
            if st.button("Approve and execute write", type="primary"):
                with st.spinner("Resuming worker and verifying result..."):
                    resumed = graph.invoke(Command(resume="approve"), config=config)
                st.session_state.run_state = resumed
                st.session_state.pending = bool(graph.get_state(config).next)
                st.rerun()
        with b:
            if st.button("Reject this write"):
                resumed = graph.invoke(Command(resume="reject"), config=config)
                st.session_state.run_state = resumed
                st.session_state.pending = bool(graph.get_state(config).next)
                st.rerun()

    if status == "completed" and state.get("result"):
        st.success("Completed and verified: the invoice was saved and then read back from the company database.")
        st.subheader("Verified database record")
        st.json(state["result"])
    if state.get("evidence"):
        st.subheader("Evidence")
        for item in state["evidence"]:
            st.write(f"- {item}")

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Company invoice system")
    with db_connect() as conn:
        rows = conn.execute("SELECT id, invoice_number, vendor, amount, currency, due_date, source_file, created_at FROM invoices ORDER BY id DESC").fetchall()
    if rows:
        st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
    else:
        st.caption("No invoices saved yet. Run the worker and approve a valid invoice.")
with right:
    st.subheader("Audit trail")
    with db_connect() as conn:
        logs = conn.execute("SELECT event, details, created_at FROM audit_log ORDER BY id DESC LIMIT 20").fetchall()
    if logs:
        st.dataframe([dict(r) for r in logs], use_container_width=True, hide_index=True)
    else:
        st.caption("Audit events appear after writes and verification.")
