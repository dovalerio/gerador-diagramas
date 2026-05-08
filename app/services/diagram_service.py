"""
DiagramService: orchestrates the full v2 pipeline.
  input (Mermaid string or YAML string)
    → parse → GraphModel
    → layout → LayoutResult
    → render → SVG string
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from parsers.mermaid.parser import parse_mermaid
from parsers.yaml_parser.adapters import yaml_to_graph
from layout.graphviz.engine import compute_layout
from render.svg_renderer import render_svg


@dataclass
class DiagramResult:
    svg: str
    title: str
    alt: str


def _is_mermaid(source: str) -> bool:
    first = source.strip().splitlines()[0].strip().lower()
    return (
        first.startswith('flowchart')
        or first.startswith('graph ')
        or first == 'sequencediagram'
        or first == 'classdiagram'
    )


class DiagramService:
    def generate(self, source: str) -> DiagramResult:
        """
        Parse source (Mermaid or YAML), compute layout, render SVG.
        Raises ValueError on bad input, RuntimeError on layout failure.
        """
        source = source.strip()
        if not source:
            raise ValueError("Input source is empty")

        if _is_mermaid(source):
            model = parse_mermaid(source)
        else:
            model = yaml_to_graph(source)

        title = str(model.metadata.get('title', ''))
        alt   = str(model.metadata.get('alt', ''))

        layout = compute_layout(model)
        svg    = render_svg(layout, title=title, alt=alt)

        return DiagramResult(svg=svg, title=title, alt=alt)
