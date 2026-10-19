"""Tests for RelayMiddleware (instructions.md §2.2): a specialist's block reaches the
user without another orchestrator model call."""
import asyncio

import pytest
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from agent.relay import RelayMiddleware, extract_block, relay_text

BLOCK = "## Gap analysis\n\nMatch score: 72%\n\nReply \"confirm\" or tell me what to change."
REPLY = ("STAGE_DONE: S0, S1\nFILES: company_brief.md, gap_analysis.md\nSTATE: S1_gap_analysis\n\n"
         f"=== USER_INPUT_NEEDED ===\n{BLOCK}\n=== END ===")


def _call(name, call_id):
    return {"name": name, "args": {"description": "x", "subagent_type": "resume-tailor"},
            "id": call_id, "type": "tool_call"}


def _turn(*results, calls=None):
    """History ending in one orchestrator tool turn. results: (call_id, text) pairs."""
    calls = calls or [_call("task", cid) for cid, _ in results]
    return [HumanMessage("tailor my resume"), AIMessage("", tool_calls=calls),
            *[ToolMessage(text, tool_call_id=cid) for cid, text in results]]


# ---------- block extraction ----------

def test_extract_user_input_needed_block():
    assert extract_block(REPLY) == BLOCK


def test_extract_final_block():
    assert extract_block("STATE: done\n\n=== FINAL ===\nWrote /x.pdf\n=== END ===") == "Wrote /x.pdf"


@pytest.mark.parametrize("text", [
    "STAGE_DONE: S0\nI wrote the brief.",                        # no block
    "=== USER_INPUT_NEEDED ===\nquestions but no end marker",     # unterminated
    "=== USER_INPUT_NEEDED ===\n\n=== END ===",                   # empty block
])
def test_extract_returns_none_without_a_complete_block(text):
    assert extract_block(text) is None


# ---------- which turns get relayed ----------

def test_relays_task_result_block():
    assert relay_text(_turn(("c1", REPLY))) == BLOCK


def test_no_relay_when_task_reply_lacks_block():
    # The orchestrator prompt's retry rule handles this case, so the model must run.
    assert relay_text(_turn(("c1", "STAGE_DONE: S0\nOops, no block."))) is None


def test_no_relay_for_non_task_tools():
    msgs = _turn(("c1", REPLY), calls=[_call("load_application", "c1")])
    assert relay_text(msgs) is None


def test_no_relay_when_last_message_is_not_a_tool_result():
    assert relay_text([HumanMessage("hi")]) is None
    assert relay_text(_turn(("c1", REPLY)) + [AIMessage("done")]) is None


def test_relay_ignores_parallel_non_task_results():
    calls = [_call("load_application", "c0"), _call("task", "c1")]
    assert relay_text(_turn(("c0", "app_dir: /applications/x"), ("c1", REPLY), calls=calls)) == BLOCK


def test_parallel_task_blocks_are_joined_in_order():
    second = REPLY.replace(BLOCK, "Second block")
    assert relay_text(_turn(("c1", REPLY), ("c2", second))) == f"{BLOCK}\n\n---\n\nSecond block"


def test_no_relay_if_any_parallel_task_lacks_block():
    assert relay_text(_turn(("c1", REPLY), ("c2", "no block here"))) is None


def test_before_model_returns_message_and_jump():
    update = RelayMiddleware().before_model({"messages": _turn(("c1", REPLY))}, runtime=None)
    assert update["jump_to"] == "end"
    assert [m.content for m in update["messages"]] == [BLOCK]


def test_before_model_does_nothing_without_block():
    assert RelayMiddleware().before_model({"messages": [HumanMessage("hi")]}, runtime=None) is None


# ---------- end to end through a real agent graph ----------

class _FakeModel(GenericFakeChatModel):
    calls: int = 0

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, *args, **kwargs):   # the async path delegates here too
        self.calls += 1
        return super()._generate(*args, **kwargs)


@tool
def task(description: str, subagent_type: str) -> str:
    """Stand-in for deepagents' task tool."""
    return REPLY


def _agent(model):
    return create_agent(model=model, tools=[task], middleware=[RelayMiddleware()])


def _model():
    return _FakeModel(messages=iter([
        AIMessage("", tool_calls=[_call("task", "c1")]),
        AIMessage("RE-TYPED BY THE MODEL"),   # must never be produced
    ]))


def test_agent_ends_turn_with_block_and_one_model_call():
    model = _model()
    out = _agent(model).invoke({"messages": [HumanMessage("tailor my resume")]})
    assert out["messages"][-1].content == BLOCK
    assert isinstance(out["messages"][-1], AIMessage)
    assert model.calls == 1


def test_agent_relay_works_async():
    # `langgraph dev` runs the graph async.
    model = _model()
    out = asyncio.run(_agent(model).ainvoke({"messages": [HumanMessage("tailor my resume")]}))
    assert out["messages"][-1].content == BLOCK
    assert model.calls == 1


def test_agent_without_block_still_calls_model():
    @tool("task")
    def bare_task(description: str, subagent_type: str) -> str:
        """Stand-in task tool whose reply has no block."""
        return "STAGE_DONE: S0\nNo block."

    model = _model()
    agent = create_agent(model=model, tools=[bare_task], middleware=[RelayMiddleware()])
    out = agent.invoke({"messages": [HumanMessage("tailor my resume")]})
    assert out["messages"][-1].content == "RE-TYPED BY THE MODEL"
    assert model.calls == 2


def test_deep_agent_task_round_trip():
    # Real deepagents `task` tool and subagent: its ToolMessage carries no tool name.
    from deepagents import create_deep_agent
    sub = _FakeModel(messages=iter([AIMessage(REPLY)]))
    orch = _model()
    agent = create_deep_agent(
        model=orch, middleware=[RelayMiddleware()],
        subagents=[{"name": "resume-tailor", "description": "d", "system_prompt": "s",
                    "model": sub, "tools": []}])
    out = agent.invoke({"messages": [HumanMessage("tailor my resume")]})
    assert out["messages"][-1].content == BLOCK
    assert (orch.calls, sub.calls) == (1, 1)


def test_orchestrator_graph_has_relay(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")  # model is built, never called
    from agent.graph import agent
    assert "RelayMiddleware.before_model" in agent.get_graph().nodes
