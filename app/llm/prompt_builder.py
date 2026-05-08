"""
Builds system + user prompts that ask the LLM to produce Mermaid DSL.
"""
from __future__ import annotations

_SUPPORTED_TYPES = (
    "flowchart LR/TD",
    "sequenceDiagram",
    "classDiagram",
)

_SYSTEM_PROMPT = """\
You are an expert software architect. Your task is to generate a Mermaid diagram based on the user's description.

Rules:
- Output ONLY valid Mermaid syntax — no markdown fences, no explanations.
- Use one of the supported diagram types: flowchart, sequenceDiagram, classDiagram.
- For flowcharts prefer `flowchart LR` unless the description implies top-down flow.
- Keep node IDs short (alphanumeric, no spaces). Use [Label] for box, (Label) for rounded, {Label} for diamond, ((Label)) for circle.
- Use -->|label| for labelled arrows, --> for plain arrows.
- Maximum 20 nodes. Prefer clarity over completeness.
- Do not add comments or extra text — only the diagram source.
"""


def build_mermaid_prompt(description: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a Mermaid generation request."""
    user = f"Generate a Mermaid diagram for the following description:\n\n{description.strip()}"
    return _SYSTEM_PROMPT, user
