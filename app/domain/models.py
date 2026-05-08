"""
Modelo canônico de grafo — independente de parser, layout e renderer.
Toda renderização parte desta representação intermediária.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class GraphNode:
    id: str
    label: str
    shape: str = "box"          # box | rounded | diamond | circle | cylinder
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    label: str = ""
    style: str = "solid"        # solid | dashed | thick | line
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphModel:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── consultas de conectividade ─────────────────────────────────────────

    def get_connected_node_ids(self, node_id: str) -> List[str]:
        seen = set()
        for e in self.edges:
            if e.source == node_id:
                seen.add(e.target)
            elif e.target == node_id:
                seen.add(e.source)
        return list(seen)

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.source == node_id]

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.target == node_id]

    def get_all_edges_for_node(self, node_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.source == node_id or e.target == node_id]

    def node_label(self, node_id: str) -> str:
        return self.nodes[node_id].label if node_id in self.nodes else node_id
