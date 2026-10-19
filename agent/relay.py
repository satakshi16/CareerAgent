"""RelayMiddleware: shows a specialist's block to the user with no extra model call (§2.2).

A subagent's reply comes back to the orchestrator as a `task` tool result. Without
this, the orchestrator model would re-type the whole block (often thousands of
tokens) as its reply. This hook runs before the orchestrator's next model call,
copies the block out of the tool result, and ends the turn.

If any `task` result in the turn has no complete block, nothing happens and the
model runs as usual, so the prompt's "call the specialist again" rule still applies.
"""
import re
from typing import Any

from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

_BLOCK_RE = re.compile(r"=== (?:USER_INPUT_NEEDED|FINAL) ===\s*(.*?)\s*=== END ===", re.DOTALL)


def extract_block(text: str) -> str | None:
    """Content between the block markers, or None if there's no non-empty block."""
    m = _BLOCK_RE.search(text or "")
    return m.group(1) if m and m.group(1) else None


def relay_text(messages: list[BaseMessage]) -> str | None:
    """The text to show the user if this turn's tool results are all-blocks `task` replies."""
    start = len(messages)
    while start and isinstance(messages[start - 1], ToolMessage):
        start -= 1
    if start == len(messages) or not start or not isinstance(messages[start - 1], AIMessage):
        return None
    # deepagents' task ToolMessage has no `name`, so match on the call ids.
    task_ids = [c["id"] for c in messages[start - 1].tool_calls if c["name"] == "task"]
    results = {m.tool_call_id: m for m in messages[start:]}
    if not task_ids or not all(cid in results for cid in task_ids):
        return None
    blocks = [extract_block(results[cid].text) for cid in task_ids]
    return None if None in blocks else "\n\n---\n\n".join(blocks)


class RelayMiddleware(AgentMiddleware):
    """Orchestrator only: ends the turn with the specialist's block, copied exactly."""

    @hook_config(can_jump_to=["end"])
    def before_model(self, state, runtime) -> dict[str, Any] | None:
        text = relay_text(state["messages"])
        if text is None:
            return None
        return {"messages": [AIMessage(content=text)], "jump_to": "end"}
