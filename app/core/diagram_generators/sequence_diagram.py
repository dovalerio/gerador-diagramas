"""
Gerador de diagramas de sequência.
"""
import graphviz
from typing import Dict, Any


def generate_sequence_diagram(data: Dict[str, Any], language: str = 'pt') -> graphviz.Digraph:
    """
    Gera um diagrama de sequência usando Graphviz.

    Args:
        data: Dados para o diagrama
        language: Idioma dos campos ('pt' para português, 'en' para inglês)

    Returns:
        graphviz.Digraph: Objeto do diagrama
    """
    if language == 'en':
        title_field, objects_field, messages_field = 'title', 'objects', 'messages'
        from_field, to_field, msg_field = 'from', 'to', 'message'
        name_field = 'name'
    else:
        title_field, objects_field, messages_field = 'titulo', 'objetos', 'mensagens'
        from_field, to_field, msg_field = 'de', 'para', 'mensagem'
        name_field = 'nome'

    title = data.get(title_field, 'Diagrama de Sequência')
    dot = graphviz.Digraph(comment=title, graph_attr={'rankdir': 'TB'})

    for obj in data.get(objects_field, []):
        dot.node(obj[name_field], shape='box')

    for message in data.get(messages_field, []):
        dot.edge(
            message[from_field],
            message[to_field],
            label=message.get(msg_field, ''),
            arrowhead='normal',
        )

    return dot
