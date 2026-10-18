"""Builds and exports `agent`, the career orchestrator served by `langgraph dev`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, for `agent.*` imports

from deepagents import FilesystemPermission, create_deep_agent  # noqa: E402
from deepagents.backends import FilesystemBackend  # noqa: E402

from agent.config import AGENTS_MD, MODEL, REPO_ROOT, load_prompt, virtual  # noqa: E402
from agent.subagents import SHARED_SKILLS, SUBAGENTS  # noqa: E402
from agent.tools.applications import create_application, load_application  # noqa: E402
from agent.tools.search import internet_search, web_extract  # noqa: E402

backend = FilesystemBackend(root_dir=REPO_ROOT, virtual_mode=True)  # agent sees "/" = repo root

# File safety (§4.5), enforced at the tool level. First matching rule wins.
# data/ changes only through append_career_fact; state.json only through
# update_application_state. Custom tools write directly and aren't affected.
PERMISSIONS = [
    FilesystemPermission(operations=["read", "write"], paths=["/.env", "/.env.*"], mode="deny"),
    FilesystemPermission(
        operations=["write"],
        paths=["/data/**", "/applications/*/state.json", "/PDFResumeGenerator/**",
               "/agent/**", "/skills/**", "/tests/**", "/instructions.md", "/langgraph.json"],
        mode="deny",
    ),
]

agent = create_deep_agent(
    model=MODEL,
    tools=[internet_search, web_extract, create_application, load_application],
    system_prompt=load_prompt("orchestrator.md"),
    subagents=SUBAGENTS,
    backend=backend,
    skills=[SHARED_SKILLS],  # orchestrator sees shared skills only
    memory=[virtual(AGENTS_MD)],
    permissions=PERMISSIONS,  # inherited by subagents that don't set their own
    # No interrupt_on: render_resume_pdf runs its own plain-text approval gate.
    name="career-orchestrator",
)
