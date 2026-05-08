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

# Splits on arrow-only token (no embedded label).
# Order matters: longer patterns must come first.
_ARROW_ONLY_RE = re.compile(
    r'(={2,}>|-\.->|-->>|-->|---|->>|->)'
)

_EDGE_COUNTER = 0


def _next_edge_id() -> str:
    global _EDGE_COUNTER
    _EDGE_COUNTER += 1
    return f"e{_EDGE_COUNTER}"


def _strip_inline_label(token: str) -> Tuple[str, str]:
    """Strip a leading |label| prefix from a node token.
    Returns (label, remaining_node_token).
    e.g. '|SQL| C[(Banco)]' → ('SQL', 'C[(Banco)]')
    """
    m = re.match(r'^\s*\|([^|]*)\|\s*(.*)', token)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', token.strip()


def _parse_flowchart(lines: list[str]) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'flowchart'})

    _STANDALONE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)(\[.*?\]|\(.*?\)|\{.*?\})\s*$')

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue

        parts = _ARROW_ONLY_RE.split(line)
        if len(parts) >= 3:
            # parts alternates: [node_token, arrow, node_token, arrow, ...]
            raw_nodes: list[str] = []
            arrows: list[str] = []
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    raw_nodes.append(part.strip())
                else:
                    arrows.append(part.strip())

            # Resolve nodes: node tokens may have a leading |label| when they
            # are the right-hand side of a labelled arrow (B -->|lbl| C).
            # The label belongs to the preceding edge, not the node.
            edge_labels: list[str] = [''] * len(arrows)
            resolved: list[str] = [raw_nodes[0]]   # left side never has prefix
            for idx in range(len(arrows)):
                right_raw = raw_nodes[idx + 1] if idx + 1 < len(raw_nodes) else ''
                lbl, node_tok = _strip_inline_label(right_raw)
                if lbl:
                    edge_labels[idx] = lbl
                resolved.append(node_tok)

            # Register nodes
            node_ids: list[str] = []
            for tok in resolved:
                if not tok:
                    node_ids.append('')
                    continue
                nid, label, shape = _parse_node_token(tok)
                if nid not in model.nodes:
                    model.nodes[nid] = GraphNode(id=nid, label=label, shape=shape)
                elif label != nid:
                    model.nodes[nid].label = label
                    model.nodes[nid].shape = shape
                node_ids.append(nid)

            # Build edges
            for idx, arrow in enumerate(arrows):
                if idx < len(node_ids) - 1 and node_ids[idx] and node_ids[idx + 1]:
                    style, _ = _parse_edge_label(arrow)
                    model.edges.append(GraphEdge(
                        id=_next_edge_id(),
                        source=node_ids[idx],
                        target=node_ids[idx + 1],
                        label=edge_labels[idx],
                        style=style,
                    ))
        else:
            m = _STANDALONE_RE.match(line)
            if m:
                nid, label, shape = _parse_node_token(line.strip())
                if nid not in model.nodes:
                    model.nodes[nid] = GraphNode(id=nid, label=label, shape=shape)

    return model


# ── sequenceDiagram parser ────────────────────────────────────────────────────

_SEQ_MSG_RE = re.compile(
    r'^(\w[\w\s]*?)\s*(->>|-->>|->|-->|-x|--x)\s*(\w[\w\s]*):\s*(.*)$'
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
