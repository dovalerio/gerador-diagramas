"""
Mermaid DSL parser → GraphModel.
Supports: flowchart/graph, sequenceDiagram, classDiagram.
"""
from __future__ import annotations
import re
from typing import Tuple, Optional

from domain.models import GraphModel, GraphNode, GraphEdge

# ── shape detection from Mermaid node syntax ──────────────────────────────────

_SHAPE_PATTERNS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r'^\(\((.+)\)\)$'), 'circle'),      # ((text))
    (re.compile(r'^\[\((.+)\)\]$'), 'cylinder'),    # [(text)]
    (re.compile(r'^\{(.+)\}$'),     'diamond'),     # {text}
    (re.compile(r'^\((.+)\)$'),     'rounded'),     # (text)
    (re.compile(r'^\[(.+)\]$'),     'box'),         # [text]
    (re.compile(r'^>(.+)\]$'),      'box'),         # >text]  asymmetric — treat as box
    (re.compile(r'^/(.+)/$'),       'box'),         # /text/  parallelogram
]


def _parse_node_token(token: str) -> Tuple[str, str, str]:
    """Return (node_id, label, shape) from a token like 'A[My Label]' or bare 'A'."""
    # Inline node definition: id followed immediately by shape delimiters
    m = re.match(r'^([A-Za-z0-9_]+)(.+)$', token)
    if m:
        node_id = m.group(1)
        rest = m.group(2).strip()
        for pattern, shape in _SHAPE_PATTERNS:
            sm = pattern.match(rest)
            if sm:
                return node_id, sm.group(1).strip(), shape
        # Unrecognised wrapper — use rest as label with box
        return node_id, rest, 'box'
    return token, token, 'box'


# ── arrow / edge style patterns ───────────────────────────────────────────────

_ARROW_PATTERNS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r'==(?:[^=].*?)?==>'), 'thick'),
    (re.compile(r'-\.->'),             'dashed'),
    (re.compile(r'-->'),               'solid'),
    (re.compile(r'---'),               'line'),
    (re.compile(r'->'),                'solid'),
]


def _parse_edge_label(arrow_raw: str) -> Tuple[str, str]:
    """Return (style, label) extracted from the full arrow token."""
    style = 'solid'
    for pattern, s in _ARROW_PATTERNS:
        if pattern.search(arrow_raw):
            style = s
            break
    # label sits between | | e.g. -->|label|
    lm = re.search(r'\|([^|]+)\|', arrow_raw)
    label = lm.group(1).strip() if lm else ''
    return style, label


# ── flowchart parser ──────────────────────────────────────────────────────────

# Matches the full arrow section including optional inline label:
#   --> , -->|text| , -. -> , === ==> , etc.
_FULL_ARROW_RE = re.compile(
    r'(={2,}(?:[^=].*?)?={2,}>|-\.->|--(?:\|[^|]*\|)?->?|->|---)'
)

_EDGE_COUNTER = 0


def _next_edge_id() -> str:
    global _EDGE_COUNTER
    _EDGE_COUNTER += 1
    return f"e{_EDGE_COUNTER}"


def _parse_flowchart(lines: list[str]) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'flowchart'})

    # Standalone node definition: id[label] on its own line
    _STANDALONE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)(\[.*?\]|\(.*?\)|\{.*?\})\s*$')

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue

        # Split by full arrow to detect edges
        parts = _FULL_ARROW_RE.split(line)
        if len(parts) >= 3:
            # parts: [left, arrow, right, arrow, right, ...]
            tokens = []
            i = 0
            while i < len(parts):
                tokens.append(('node', parts[i].strip()))
                if i + 1 < len(parts):
                    tokens.append(('arrow', parts[i + 1].strip()))
                i += 2

            prev_id: Optional[str] = None
            for kind, value in tokens:
                if kind == 'node' and value:
                    nid, label, shape = _parse_node_token(value)
                    if nid not in model.nodes:
                        model.nodes[nid] = GraphNode(id=nid, label=label, shape=shape)
                    elif label != nid:
                        # Update label/shape if we now have more info
                        model.nodes[nid].label = label
                        model.nodes[nid].shape = shape
                    prev_id = nid
                elif kind == 'arrow':
                    # peek at the next node token
                    pass

            # Build edges between consecutive node pairs
            node_ids = [v for k, v in tokens if k == 'node' and v]
            arrow_tokens = [v for k, v in tokens if k == 'arrow']
            for idx, arrow in enumerate(arrow_tokens):
                if idx < len(node_ids) - 1:
                    style, label = _parse_edge_label(arrow)
                    src_id = _parse_node_token(node_ids[idx])[0]
                    tgt_id = _parse_node_token(node_ids[idx + 1])[0]
                    model.edges.append(GraphEdge(
                        id=_next_edge_id(),
                        source=src_id,
                        target=tgt_id,
                        label=label,
                        style=style,
                    ))
        else:
            # Standalone node definition
            m = _STANDALONE_RE.match(line)
            if m:
                nid, label, shape = _parse_node_token(line.strip())
                if nid not in model.nodes:
                    model.nodes[nid] = GraphNode(id=nid, label=label, shape=shape)

    return model


# ── sequenceDiagram parser ────────────────────────────────────────────────────

_SEQ_MSG_RE = re.compile(
    r'^(\w[\w\s]*)(->>?--?|-->>|->|-x|-->)\s*(\w[\w\s]*):\s*(.*)$'
)
_SEQ_PARTICIPANT_RE = re.compile(r'^participant\s+(\w[\w\s]*)(?:\s+as\s+(.+))?$')
_SEQ_ACTOR_RE = re.compile(r'^actor\s+(\w[\w\s]*)(?:\s+as\s+(.+))?$')


def _parse_sequence(lines: list[str]) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'sequence'})
    order = 0

    def ensure_participant(name: str, label: str = '') -> None:
        nonlocal order
        if name not in model.nodes:
            model.nodes[name] = GraphNode(
                id=name, label=label or name, shape='box',
                metadata={'order': order}
            )
            order += 1

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue

        m = _SEQ_PARTICIPANT_RE.match(line)
        if m:
            ensure_participant(m.group(1).strip(), (m.group(2) or '').strip())
            continue

        m = _SEQ_ACTOR_RE.match(line)
        if m:
            ensure_participant(m.group(1).strip(), (m.group(2) or '').strip())
            continue

        m = _SEQ_MSG_RE.match(line)
        if m:
            src, arrow_raw, tgt, msg = (x.strip() for x in m.groups())
            ensure_participant(src)
            ensure_participant(tgt)
            style = 'dashed' if '--' in arrow_raw else 'solid'
            model.edges.append(GraphEdge(
                id=_next_edge_id(),
                source=src, target=tgt,
                label=msg, style=style,
            ))

    return model


# ── classDiagram parser ───────────────────────────────────────────────────────

_CLASS_DECL_RE = re.compile(r'^class\s+(\w+)(?:\s*\{)?$')
_CLASS_REL_RE = re.compile(
    r'^(\w+)\s*(<\|--|<\|\.\.|\*--|o--|-->|\.\.>|--|\.\.)\s*(\w+)\s*(?::\s*(.*))?$'
)
_CLASS_MEMBER_RE = re.compile(r'^([+\-#~]?)(.+)$')

_RELATION_STYLE = {
    '<|--': 'solid', '<|..': 'dashed', '*--': 'solid',
    'o--': 'solid', '-->': 'solid', '..>': 'dashed',
    '--': 'line', '..': 'dashed',
}


def _parse_classdiagram(lines: list[str]) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'class'})
    current_class: Optional[str] = None

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue

        if line == '}':
            current_class = None
            continue

        m = _CLASS_DECL_RE.match(line)
        if m:
            cname = m.group(1)
            if cname not in model.nodes:
                model.nodes[cname] = GraphNode(id=cname, label=cname, shape='box',
                                               metadata={'members': []})
            current_class = cname
            continue

        m = _CLASS_REL_RE.match(line)
        if m:
            src, rel, tgt, lbl = m.group(1), m.group(2), m.group(3), (m.group(4) or '')
            for cls in (src, tgt):
                if cls not in model.nodes:
                    model.nodes[cls] = GraphNode(id=cls, label=cls, shape='box',
                                                 metadata={'members': []})
            style = _RELATION_STYLE.get(rel.strip(), 'solid')
            model.edges.append(GraphEdge(
                id=_next_edge_id(),
                source=src, target=tgt,
                label=lbl.strip(), style=style,
                metadata={'relation': rel.strip()},
            ))
            current_class = None
            continue

        if current_class and line not in ('{', '}'):
            model.nodes[current_class].metadata.setdefault('members', []).append(line)

    return model


# ── public entry point ────────────────────────────────────────────────────────

def parse_mermaid(source: str) -> GraphModel:
    """Parse a Mermaid diagram string into a GraphModel."""
    lines = source.strip().splitlines()
    if not lines:
        raise ValueError("Empty Mermaid source")

    header = lines[0].strip().lower()
    body = lines[1:]

    if header.startswith('flowchart') or header.startswith('graph'):
        return _parse_flowchart(body)
    if header == 'sequencediagram':
        return _parse_sequence(body)
    if header == 'classdiagram':
        return _parse_classdiagram(body)

    raise ValueError(f"Unsupported Mermaid diagram type: '{lines[0].strip()}'")
