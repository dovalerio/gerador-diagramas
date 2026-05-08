"""
Gerador de diagramas de casos de uso.
"""
import graphviz
from typing import Dict, Any


def generate_use_case_diagram(data: Dict[str, Any], language: str = 'pt') -> graphviz.Digraph:
    """
    Gera um diagrama de casos de uso usando Graphviz.

    Args:
        data: Dados para o diagrama
        language: Idioma dos campos ('pt' para português, 'en' para inglês)

    Returns:
        graphviz.Digraph: Objeto do diagrama
    """
    if language == 'en':
        title_field = 'title'
        actors_field, use_cases_field, relationships_field = 'actors', 'use_cases', 'relationships'
        from_field, to_field, type_field = 'from', 'to', 'type'
        name_field = 'name'
    else:
        title_field = 'titulo'
        actors_field, use_cases_field, relationships_field = 'atores', 'casos_de_uso', 'relacionamentos'
        from_field, to_field, type_field = 'de', 'para', 'tipo'
        name_field = 'nome'

    title = data.get(title_field, 'Diagrama de Casos de Uso')
    dot = graphviz.Digraph(comment=title, graph_attr={'rankdir': 'LR'})

    for actor in data.get(actors_field, []):
        dot.node(actor[name_field], shape='oval')

    for use_case in data.get(use_cases_field, []):
        dot.node(use_case[name_field], shape='ellipse')

    for relationship in data.get(relationships_field, []):
        dot.edge(
            relationship[from_field],
            relationship[to_field],
            label=relationship.get(type_field, ''),
        )

    return dot
