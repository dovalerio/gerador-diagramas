"""
Gerador de diagramas de implantação.
"""
import graphviz
from typing import Dict, Any


_NODE_STYLES = {
    'server': {'shape': 'box3d', 'style': 'filled', 'fillcolor': 'lightgreen'},
    'device': {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'moccasin'},
    'database': {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'lightyellow'},
    'artifact': {'shape': 'rectangle', 'style': 'filled', 'fillcolor': 'lavender'},
    # aliases PT
    'servidor': {'shape': 'box3d', 'style': 'filled', 'fillcolor': 'lightgreen'},
    'dispositivo': {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'moccasin'},
    'banco de dados': {'shape': 'cylinder', 'style': 'filled', 'fillcolor': 'lightyellow'},
    'artefato': {'shape': 'rectangle', 'style': 'filled', 'fillcolor': 'lavender'},
}


def generate_deployment_diagram(data: Dict[str, Any], language: str = 'pt') -> graphviz.Digraph:
    """
    Gera um diagrama de implantação usando Graphviz.

    Args:
        data: Dados para o diagrama
        language: Idioma dos campos ('pt' para português, 'en' para inglês)

    Returns:
        graphviz.Digraph: Objeto do diagrama
    """
    if language == 'en':
        title_field = 'title'
        nodes_field, connections_field = 'nodes', 'connections'
        from_field, to_field, label_field = 'from', 'to', 'event'
        name_field, type_field, container_field = 'name', 'type', 'container'
    else:
        title_field = 'titulo'
        nodes_field, connections_field = 'nos', 'conexoes'
        from_field, to_field, label_field = 'de', 'para', 'evento'
        name_field, type_field, container_field = 'nome', 'tipo', 'container'

    title = data.get(title_field, 'Diagrama de Implantação')
    dot = graphviz.Digraph(comment=title, graph_attr={'rankdir': 'LR'})

    for node in data.get(nodes_field, []):
        node_type = node.get(type_field, '')
        style = _NODE_STYLES.get(node_type.lower(), {'shape': 'box'})
        dot.node(node[name_field], **style)

        if node.get(container_field):
            dot.edge(node[container_field], node[name_field], style='dashed')

    for connection in data.get(connections_field, []):
        dot.edge(
            connection[from_field],
            connection[to_field],
            label=connection.get(label_field, ''),
            arrowhead='normal',
        )

    return dot
