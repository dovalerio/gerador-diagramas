"""
Layout engine: GraphModel → LayoutResult.

Uses `dot -Tplain` to compute node positions and edge waypoints, then
converts from Graphviz inches to SVG pixels (96 DPI) and flips the Y axis
(Graphviz: Y=0 at bottom; SVG: Y=0 at top).
"""
from __future__ import annotations
import re
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import graphviz

from domain.models import GraphModel, GraphNode

_DPI = 96         # SVG pixels per inch
_PAD_PX = 20      # padding around the computed bounding box

# Graphviz shape map
_SHAPE_MAP = {
    'box':      'box',
    'rounded':  'box',          # style=rounded applied separately
    'diamond':  'diamond',
    'circle':   'circle',
    'cylinder': 'cylinder',
}

_STYLE_MAP = {
    'rounded': {'shape': 'box', 'style': 'rounded'},
    'cylinder': {'shape': 'cylinder'},
}


@dataclass
class NodeLayout:
    id: str
    x: float        # SVG pixels, centre
    y: float        # SVG pixels, centre
    width: float    # SVG pixels
    height: float   # SVG pixels
    label: str
    shape: str


@dataclass
class EdgeLayout:
    id: str
    source: str
    target: str
    label: str
    style: str
    # List of (x, y) control points in SVG pixels
    points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class LayoutResult:
    nodes: Dict[str, NodeLayout] = field(default_factory=dict)
    edges: List[EdgeLayout] = field(default_factory=list)
    width: float = 0.0      # total SVG canvas width in pixels
    height: float = 0.0     # total SVG canvas height in pixels


# ── plain-text format parser ──────────────────────────────────────────────────

# graph <scale> <width_in> <height_in>
_GRAPH_RE = re.compile(r'^graph\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)')
# node <name> <x_in> <y_in> <w_in> <h_in> <label> ...
_NODE_RE  = re.compile(r'^node\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+("(?:[^"]|\\")*"|\S+)')
# edge <src> <dst> <n_points> <x1> <y1> ...  [<label> <xl> <yl>]
_EDGE_RE  = re.compile(r'^edge\s+(\S+)\s+(\S+)\s+(\d+)\s+(.+)$')


def _unquote(s: str) -> str:
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1].replace('\\"', '"')
    return s


def _parse_plain(plain_text: str, graph_h_px: float) -> Tuple[
        Dict[str, Tuple[float, float, float, float, str]],
        List[Tuple[str, str, List[Tuple[float, float]]]]]:
    """
    Returns:
        nodes_info: {name: (cx_px, cy_px, w_px, h_px, label)}
        edges_info: [(src, dst, [(x_px, y_px), ...])]
    """
    nodes_info: Dict[str, Tuple[float, float, float, float, str]] = {}
    edges_info: List[Tuple[str, str, List[Tuple[float, float]]]] = []

    for line in plain_text.splitlines():
        m = _NODE_RE.match(line)
        if m:
            name = m.group(1)
            cx = float(m.group(2)) * _DPI
            # Flip Y: gv Y=0 is bottom, SVG Y=0 is top
            cy = graph_h_px - float(m.group(3)) * _DPI
            w  = float(m.group(4)) * _DPI
            h  = float(m.group(5)) * _DPI
            label = _unquote(m.group(6))
            nodes_info[name] = (cx, cy, w, h, label)
            continue

        m = _EDGE_RE.match(line)
        if m:
            src, dst = m.group(1), m.group(2)
            n = int(m.group(3))
            rest = m.group(4).split()
            pts: List[Tuple[float, float]] = []
            for i in range(n):
                px = float(rest[i * 2]) * _DPI
                py = graph_h_px - float(rest[i * 2 + 1]) * _DPI
                pts.append((px, py))
            edges_info.append((src, dst, pts))

    return nodes_info, edges_info


# ── main entry point ──────────────────────────────────────────────────────────

def compute_layout(model: GraphModel) -> LayoutResult:
    """Run Graphviz dot layout and return pixel positions for all elements."""
    dot = graphviz.Digraph(graph_attr={'rankdir': 'LR'})

    for nid, node in model.nodes.items():
        attrs = {'label': node.label}
        shape = _SHAPE_MAP.get(node.shape, 'box')
        attrs['shape'] = shape
        if node.shape == 'rounded':
            attrs['style'] = 'rounded'
        dot.node(nid, **attrs)

    for edge in model.edges:
        edge_attrs: Dict[str, str] = {}
        if edge.label:
            edge_attrs['label'] = edge.label
        if edge.style == 'dashed':
            edge_attrs['style'] = 'dashed'
        elif edge.style == 'thick':
            edge_attrs['style'] = 'bold'
        elif edge.style == 'line':
            edge_attrs['arrowhead'] = 'none'
        dot.edge(edge.source, edge.target, **edge_attrs)

    # Render to plain format via stdin (no temp files)
    plain_bytes: bytes = dot.pipe(format='plain')
    plain_text = plain_bytes.decode('utf-8', errors='replace')

    # Extract graph dimensions from first line
    graph_h_px = 0.0
    canvas_w_px = 0.0
    for line in plain_text.splitlines():
        gm = _GRAPH_RE.match(line)
        if gm:
            canvas_w_px = float(gm.group(2)) * _DPI + _PAD_PX * 2
            graph_h_px  = float(gm.group(3)) * _DPI
            break

    nodes_info, edges_info = _parse_plain(plain_text, graph_h_px)

    result = LayoutResult(
        width=canvas_w_px,
        height=graph_h_px + _PAD_PX * 2,
    )

    for nid, (cx, cy, w, h, label) in nodes_info.items():
        result.nodes[nid] = NodeLayout(
            id=nid,
            x=cx + _PAD_PX,
            y=cy + _PAD_PX,
            width=w,
            height=h,
            label=model.nodes[nid].label if nid in model.nodes else label,
            shape=model.nodes[nid].shape if nid in model.nodes else 'box',
        )

    for edge in model.edges:
        # Find matching edge from dot plain output
        pts: List[Tuple[float, float]] = []
        for src, dst, plain_pts in edges_info:
            if src == edge.source and dst == edge.target:
                pts = [(x + _PAD_PX, y + _PAD_PX) for x, y in plain_pts]
                break
        result.edges.append(EdgeLayout(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            label=edge.label,
            style=edge.style,
            points=pts,
        ))

    return result
