"""Subagent specs (instructions.md §4.4). Custom subagents don't inherit the
orchestrator's skills, so shared skills are listed explicitly.

outreach-writer (route 3) is not built yet.
"""
from agent.config import load_prompt
from agent.tools.applications import load_application, update_application_state
from agent.tools.career_facts import append_career_fact
from agent.tools.resume_pdf import check_draft, render_resume_pdf, validate_resume
from agent.tools.search import internet_search, web_extract
from agent.tools.stage_context import load_stage_context
from agent.tools.style_lint import style_lint

SHARED_SKILLS = "/skills/shared/"
RESUME_SKILLS = "/skills/resume/"
INTERVIEW_SKILLS = "/skills/interview/"

RESUME_TAILOR = {
    "name": "resume-tailor",
    "description": (
        "Tailors the master resume to one job description in stages S0-S6: company "
        "research, gap analysis, metric elicitation, truthful rewrite, ATS and hiring-manager "
        "scan, approval loop, PDF render, and optional cover letter. Runs one stage per call "
        "and returns a USER_INPUT_NEEDED or FINAL block to show the user verbatim. "
        "Call with: app_dir, stage (from state.json), and user_reply (verbatim)."
    ),
    "system_prompt": load_prompt("resume_tailor.md"),
    "tools": [
        load_stage_context, internet_search, web_extract, check_draft, validate_resume,
        render_resume_pdf, style_lint, append_career_fact, load_application,
        update_application_state,
    ],
    "skills": [SHARED_SKILLS, RESUME_SKILLS],
}

INTERVIEW_COACH = {
    "name": "interview-coach",
    "description": (
        "Prepares the candidate for one interview round (recruiter_screen, hiring_manager, "
        "technical, behavioral, or a mix): researched question bank with real-experience "
        "answers, pitch, why-this-role, gap handling, plain-language concept explanations, "
        "study resources matched to the user's study preference, and a mock drill. Runs one "
        "stage per call and returns a USER_INPUT_NEEDED block to show the user verbatim. "
        "Call with: app_dir, stage (state.json interview.stage, or I0_intake), round, "
        "study_pref, details, and user_reply (verbatim)."
    ),
    "system_prompt": load_prompt("interview_coach.md"),
    "tools": [
        load_stage_context, internet_search, web_extract, style_lint, append_career_fact,
        load_application, update_application_state,
    ],
    "skills": [SHARED_SKILLS, INTERVIEW_SKILLS],
}

# Replaces deepagents' default general-purpose subagent so nothing can write
# candidate content outside the resume-tailor's rules.
GENERAL_PURPOSE = {
    "name": "general-purpose",
    "description": (
        "Quick research helper for questions that don't belong to a route, such as "
        "looking up a company fact. Never writes resume content, cover letters, interview "
        "answers, or messages."
    ),
    "system_prompt": (
        "You answer one research question with web search and file reads, and return a "
        "short answer with source links. You never write resume content, cover letters, "
        "interview answers, or outreach messages, and you never write files."
    ),
    "tools": [internet_search, web_extract],
    "skills": [SHARED_SKILLS],
}

SUBAGENTS = [RESUME_TAILOR, INTERVIEW_COACH, GENERAL_PURPOSE]
