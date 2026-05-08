"""
SVG renderer: LayoutResult → SVG string.
Generates semantic SVG with ARIA attributes for keyboard and screen-reader access.
"""
from __future__ import annotations
import math
from typing import List, Tuple

from layout.graphviz.engine import LayoutResult, NodeLayout, EdgeLayout
from accessibility.aria import node_aria_attrs, edge_aria_attrs, attrs_to_str

# ── visual constants ──────────────────────────────────────────────────────────

_FONT = "Arial, sans-serif"
_FONT_SIZE = 13
_NODE_FILL = "#EFF6FF"
_NODE_STROKE = "#3B82F6"
_NODE_STROKE_W = 1.5
_EDGE_STROKE = "#6B7280"
_EDGE_STROKE_W = 1.5
_LABEL_COLOR = "#1F2937"
_EDGE_LABEL_COLOR = "#6B7280"
_EDGE_LABEL_SIZE = 11
_ARROW_SIZE = 8

_STROKE_DASH = {
    'solid': '',
    'dashed': '6,3',
    'thick': '',
    'line': '',
}
_STROKE_WIDTH = {
    'solid': _EDGE_STROKE_W,
    'dashed': _EDGE_STROKE_W,
    'thick': 3.0,
    'line': _EDGE_STROKE_W,
}


# ── SVG element builders ──────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """XML-escape a string for use in SVG text content or attributes."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _node_shape_svg(nl: NodeLayout) -> str:
    x, y, w, h = nl.x - nl.width / 2, nl.y - nl.height / 2, nl.width, nl.height
    stroke = f'stroke="{_NODE_STROKE}" stroke-width="{_NODE_STROKE_W}" fill="{_NODE_FILL}"'

    if nl.shape == 'circle':
        r = min(w, h) / 2
        return f'<ellipse cx="{nl.x:.1f}" cy="{nl.y:.1f}" rx="{r:.1f}" ry="{r:.1f}" {stroke}/>'

    if nl.shape == 'diamond':
        pts = (
            f"{nl.x:.1f},{(nl.y - h/2):.1f} "
            f"{(nl.x + w/2):.1f},{nl.y:.1f} "
            f"{nl.x:.1f},{(nl.y + h/2):.1f} "
            f"{(nl.x - w/2):.1f},{nl.y:.1f}"
        )
        return f'<polygon points="{pts}" {stroke}/>'

    if nl.shape == 'cylinder':
        rx, ry = w / 2, h * 0.12
        top_y = y + ry
        body_h = h - ry * 2
        return (
            f'<rect x="{x:.1f}" y="{top_y:.1f}" width="{w:.1f}" height="{body_h:.1f}" {stroke}/>'
            f'<ellipse cx="{nl.x:.1f}" cy="{top_y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" {stroke}/>'
            f'<ellipse cx="{nl.x:.1f}" cy="{(top_y + body_h):.1f}" rx="{rx:.1f}" ry="{ry:.1f}" {stroke}/>'
        )

    if nl.shape == 'rounded':
        r = min(w, h) * 0.25
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r:.1f}" ry="{r:.1f}" {stroke}/>'

    # default: box
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" {stroke}/>'


def _node_label_svg(nl: NodeLayout) -> str:
    lines = nl.label.split('\\n') if '\\n' in nl.label else [nl.label]
    line_h = _FONT_SIZE * 1.4
    total_h = line_h * len(lines)
    y_start = nl.y - total_h / 2 + _FONT_SIZE

    parts = []
    for i, line in enumerate(lines):
        cy = y_start + i * line_h
        parts.append(
            f'<text x="{nl.x:.1f}" y="{cy:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-family="{_FONT}" font-size="{_FONT_SIZE}" fill="{_LABEL_COLOR}">'
            f'{_esc(line)}</text>'
        )
    return '\n'.join(parts)


def _cubic_path(pts: List[Tuple[float, float]]) -> str:
    """Build an SVG path from a list of control points (Graphviz spline)."""
    if len(pts) < 2:
        return ''
    d = f'M {pts[0][0]:.1f} {pts[0][1]:.1f}'
    i = 1
    while i + 2 < len(pts):
        d += (f' C {pts[i][0]:.1f} {pts[i][1]:.1f},'
              f' {pts[i+1][0]:.1f} {pts[i+1][1]:.1f},'
              f' {pts[i+2][0]:.1f} {pts[i+2][1]:.1f}')
        i += 3
    while i < len(pts):
        d += f' L {pts[i][0]:.1f} {pts[i][1]:.1f}'
        i += 1
    return d


def _arrowhead_svg(pts: List[Tuple[float, float]], style: str) -> str:
    if style == 'line' or len(pts) < 2:
        return ''
    x2, y2 = pts[-1]
    x1, y1 = pts[-2]
    angle = math.atan2(y2 - y1, x2 - x1)
    a = _ARROW_SIZE
    p1 = (x2 - a * math.cos(angle - 0.4), y2 - a * math.sin(angle - 0.4))
    p2 = (x2 - a * math.cos(angle + 0.4), y2 - a * math.sin(angle + 0.4))
    pts_str = f'{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    return f'<polygon points="{pts_str}" fill="{_EDGE_STROKE}" stroke="none"/>'


def _edge_label_svg(pts: List[Tuple[float, float]], label: str) -> str:
    if not label or not pts:
        return ''
    mid = pts[len(pts) // 2]
    return (
        f'<text x="{mid[0]:.1f}" y="{(mid[1] - 4):.1f}" '
        f'text-anchor="middle" font-family="{_FONT}" '
        f'font-size="{_EDGE_LABEL_SIZE}" fill="{_EDGE_LABEL_COLOR}">'
        f'{_esc(label)}</text>'
    )


# ── public entry point ────────────────────────────────────────────────────────

def render_svg(layout: LayoutResult, title: str = '', alt: str = '') -> str:
    """Render a LayoutResult to an accessible SVG string."""
    w, h = layout.width, layout.height
    parts: List[str] = []

    # SVG root with ARIA
    aria_label = alt or title or 'Diagram'
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" '
        f'role="img" aria-label="{_esc(aria_label)}">'
    )

    if title or alt:
        parts.append(f'<title>{_esc(title or alt)}</title>')
    if alt:
        parts.append(f'<desc>{_esc(alt)}</desc>')

    # Defs: marker for arrowheads (fallback; we draw custom polygons per edge)
    parts.append('<defs><style>g[role=button]:focus { outline: 2px solid #2563EB; outline-offset: 2px; }</style></defs>')

    # ── edges (drawn below nodes) ────────────────────────────────────────────
    # Build a lookup from edge id to node labels for ARIA
    node_label = {nid: nl.label for nid, nl in layout.nodes.items()}

    for el in layout.edges:
        if not el.points:
            continue
        dash = _STROKE_DASH.get(el.style, '')
        sw = _STROKE_WIDTH.get(el.style, _EDGE_STROKE_W)
        dash_attr = f'stroke-dasharray="{dash}"' if dash else ''
        path_d = _cubic_path(el.points)
        src_lbl = node_label.get(el.source, el.source)
        tgt_lbl = node_label.get(el.target, el.target)
        aria_str = attrs_to_str(edge_aria_attrs(el.id, src_lbl, tgt_lbl, el.label))

        parts.append(f'<g {aria_str}>')
        parts.append(
            f'<path d="{path_d}" fill="none" '
            f'stroke="{_EDGE_STROKE}" stroke-width="{sw}" {dash_attr}/>'
        )
        parts.append(_arrowhead_svg(el.points, el.style))
        parts.append(_edge_label_svg(el.points, el.label))
        parts.append('</g>')

    # ── nodes ────────────────────────────────────────────────────────────────
    for nid, nl in layout.nodes.items():
        connected = [e.target if e.source == nid else e.source
                     for e in layout.edges
                     if e.source == nid or e.target == nid]
        aria_str = attrs_to_str(node_aria_attrs(nid, nl.label, connected))
        parts.append(f'<g {aria_str}>')
        parts.append(_node_shape_svg(nl))
        parts.append(_node_label_svg(nl))
        parts.append('</g>')

    parts.append('</svg>')
    return '\n'.join(parts)
