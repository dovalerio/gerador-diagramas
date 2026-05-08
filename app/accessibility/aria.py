"""
ARIA attribute helpers for semantic SVG generation.
"""
from __future__ import annotations
from typing import Dict, List


def node_aria_attrs(node_id: str, label: str, connected_ids: List[str]) -> Dict[str, str]:
    """Return ARIA attributes for an SVG node group element."""
    connected = ' '.join(connected_ids) if connected_ids else ''
    attrs: Dict[str, str] = {
        'role': 'button',
        'tabindex': '0',
        'aria-label': label,
        'data-node-id': node_id,
    }
    if connected:
        attrs['data-connected-to'] = connected
    return attrs


def edge_aria_attrs(edge_id: str, source_label: str, target_label: str, label: str) -> Dict[str, str]:
    """Return ARIA attributes for an SVG edge group element."""
    description = f"Connection from {source_label} to {target_label}"
    if label:
        description += f": {label}"
    return {
        'role': 'img',
        'aria-label': description,
        'data-edge-id': edge_id,
    }


def attrs_to_str(attrs: Dict[str, str]) -> str:
    """Serialize attribute dict to HTML attribute string."""
    parts = []
    for key, value in attrs.items():
        escaped = value.replace('"', '&quot;')
        parts.append(f'{key}="{escaped}"')
    return ' '.join(parts)
