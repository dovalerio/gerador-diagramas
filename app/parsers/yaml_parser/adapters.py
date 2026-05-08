"""
Adapters: existing YAML diagram format → GraphModel.
Each diagram type has its own adapter function.
"""
from __future__ import annotations
import re
from typing import Any, Dict

import yaml

from domain.models import GraphModel, GraphNode, GraphEdge

_EDGE_COUNTER = 0


def _eid() -> str:
    global _EDGE_COUNTER
    _EDGE_COUNTER += 1
    return f"e{_EDGE_COUNTER}"


def _slug(text: str) -> str:
    return re.sub(r'\W+', '_', text).strip('_')


# ── architecture ──────────────────────────────────────────────────────────────

def _adapt_architecture(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'architecture'})

    if lang == 'en':
        users_k, services_k, connections_k = 'users', 'services', 'connections'
        name_k, from_k, to_k, event_k = 'name', 'from', 'to', 'event'
    else:
        users_k, services_k, connections_k = 'usuarios', 'servicos', 'conexoes'
        name_k, from_k, to_k, event_k = 'nome', 'de', 'para', 'evento'

    for u in data.get(users_k, []):
        nid = _slug(u[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=u[name_k], shape='circle')

    for s in data.get(services_k, []):
        nid = _slug(s[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=s[name_k], shape='box')

    for c in data.get(connections_k, []):
        src, tgt = _slug(c[from_k]), _slug(c[to_k])
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=c.get(event_k, ''), style='solid',
        ))

    return model


# ── classes ───────────────────────────────────────────────────────────────────

def _adapt_classes(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'class'})

    if lang == 'en':
        classes_k, rels_k = 'classes', 'relationships'
        name_k, attrs_k, methods_k = 'name', 'attributes', 'methods'
        from_k, to_k, type_k = 'from', 'to', 'type'
    else:
        classes_k, rels_k = 'classes', 'relacionamentos'
        name_k, attrs_k, methods_k = 'nome', 'atributos', 'metodos'
        from_k, to_k, type_k = 'de', 'para', 'tipo'

    for cls in data.get(classes_k, []):
        nid = _slug(cls[name_k])
        model.nodes[nid] = GraphNode(
            id=nid, label=cls[name_k], shape='box',
            metadata={
                'attributes': cls.get(attrs_k, []),
                'methods': cls.get(methods_k, []),
            }
        )

    style_map = {'heranca': 'solid', 'herança': 'solid', 'inheritance': 'solid',
                 'composicao': 'solid', 'composição': 'solid', 'composition': 'solid',
                 'agregacao': 'dashed', 'agregação': 'dashed', 'aggregation': 'dashed',
                 'associacao': 'line', 'associação': 'line', 'association': 'line'}

    for rel in data.get(rels_k, []):
        src, tgt = _slug(rel[from_k]), _slug(rel[to_k])
        rtype = rel.get(type_k, '').lower()
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=rtype, style=style_map.get(rtype, 'solid'),
            metadata={'relation': rtype},
        ))

    return model


# ── sequence ──────────────────────────────────────────────────────────────────

def _adapt_sequence(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'sequence'})

    if lang == 'en':
        objects_k, messages_k = 'objects', 'messages'
        name_k, from_k, to_k, msg_k = 'name', 'from', 'to', 'message'
    else:
        objects_k, messages_k = 'objetos', 'mensagens'
        name_k, from_k, to_k, msg_k = 'nome', 'de', 'para', 'mensagem'

    for idx, obj in enumerate(data.get(objects_k, [])):
        nid = _slug(obj[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=obj[name_k], shape='box',
                                     metadata={'order': idx})

    for msg in data.get(messages_k, []):
        src, tgt = _slug(msg[from_k]), _slug(msg[to_k])
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=msg.get(msg_k, ''), style='solid',
        ))

    return model


# ── use case ──────────────────────────────────────────────────────────────────

def _adapt_usecase(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'usecase'})

    if lang == 'en':
        actors_k, usecases_k, rels_k = 'actors', 'usecases', 'relationships'
        name_k, from_k, to_k, type_k = 'name', 'from', 'to', 'type'
    else:
        actors_k, usecases_k, rels_k = 'atores', 'casos_de_uso', 'relacionamentos'
        name_k, from_k, to_k, type_k = 'nome', 'de', 'para', 'tipo'

    for actor in data.get(actors_k, []):
        nid = _slug(actor[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=actor[name_k], shape='circle')

    for uc in data.get(usecases_k, []):
        nid = _slug(uc[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=uc[name_k], shape='rounded')

    for rel in data.get(rels_k, []):
        src, tgt = _slug(rel[from_k]), _slug(rel[to_k])
        rtype = rel.get(type_k, '').lower()
        style = 'dashed' if rtype in ('include', 'extend', 'incluir', 'estender') else 'solid'
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=rtype, style=style,
        ))

    return model


# ── component ─────────────────────────────────────────────────────────────────

def _adapt_component(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'component'})

    if lang == 'en':
        comps_k, connections_k = 'components', 'connections'
        name_k, from_k, to_k, event_k = 'name', 'from', 'to', 'event'
    else:
        comps_k, connections_k = 'componentes', 'conexoes'
        name_k, from_k, to_k, event_k = 'nome', 'de', 'para', 'evento'

    for comp in data.get(comps_k, []):
        nid = _slug(comp[name_k])
        model.nodes[nid] = GraphNode(id=nid, label=comp[name_k], shape='box')

    for c in data.get(connections_k, []):
        src, tgt = _slug(c[from_k]), _slug(c[to_k])
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=c.get(event_k, ''), style='solid',
        ))

    return model


# ── deployment ────────────────────────────────────────────────────────────────

def _adapt_deployment(data: Dict[str, Any], lang: str) -> GraphModel:
    global _EDGE_COUNTER
    _EDGE_COUNTER = 0
    model = GraphModel(metadata={'type': 'deployment'})

    if lang == 'en':
        nodes_k, connections_k = 'nodes', 'connections'
        name_k, type_k, from_k, to_k, event_k = 'name', 'type', 'from', 'to', 'event'
    else:
        nodes_k, connections_k = 'nos', 'conexoes'
        name_k, type_k, from_k, to_k, event_k = 'nome', 'tipo', 'de', 'para', 'evento'

    shape_map = {
        'server': 'box', 'servidor': 'box',
        'database': 'cylinder', 'banco de dados': 'cylinder',
        'device': 'box', 'dispositivo': 'box',
        'artifact': 'box', 'artefato': 'box',
    }

    for node in data.get(nodes_k, []):
        nid = _slug(node[name_k])
        ntype = node.get(type_k, '').lower()
        shape = shape_map.get(ntype, 'box')
        model.nodes[nid] = GraphNode(id=nid, label=node[name_k], shape=shape,
                                     metadata={'node_type': ntype})

    for c in data.get(connections_k, []):
        src, tgt = _slug(c[from_k]), _slug(c[to_k])
        model.edges.append(GraphEdge(
            id=_eid(), source=src, target=tgt,
            label=c.get(event_k, ''), style='solid',
        ))

    return model


# ── dispatcher ────────────────────────────────────────────────────────────────

_ADAPTERS = {
    'arquitetura': _adapt_architecture, 'architecture': _adapt_architecture,
    'classes':     _adapt_classes,      'class':        _adapt_classes,
    'sequencia':   _adapt_sequence,     'sequence':     _adapt_sequence,
    'casos de uso': _adapt_usecase,     'use case':     _adapt_usecase,
    'componentes': _adapt_component,    'components':   _adapt_component,
    'implantacao': _adapt_deployment,   'deployment':   _adapt_deployment,
    'implantação': _adapt_deployment,
}


def yaml_to_graph(yaml_source: str) -> GraphModel:
    """Parse YAML source and return a GraphModel."""
    data = yaml.safe_load(yaml_source)
    if not isinstance(data, dict):
        raise ValueError("YAML must be a mapping at the top level")

    diagrama = data.get('diagrama') or data.get('diagram')
    if not diagrama:
        raise ValueError("YAML must have a 'diagrama' or 'diagram' key")

    dtype = (diagrama.get('tipo') or diagrama.get('type') or '').lower().strip()
    lang = 'en' if diagrama.get('type') else 'pt'

    adapter = _ADAPTERS.get(dtype)
    if not adapter:
        raise ValueError(f"Unsupported diagram type: '{dtype}'")

    model = adapter(diagrama, lang)
    model.metadata['title'] = (
        diagrama.get('titulo') or diagrama.get('title') or dtype
    )
    model.metadata['alt'] = (
        diagrama.get('descricao_alternativa')
        or diagrama.get('alternative_description')
        or ''
    )
    return model
