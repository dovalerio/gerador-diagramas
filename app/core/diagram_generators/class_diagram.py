"""
Gerador de diagramas de classes.
"""
import graphviz
from typing import Dict, Any


def _build_class_label(class_name: str, class_data: Dict[str, Any], language: str) -> str:
    attributes_field = 'attributes' if language == 'en' else 'atributos'
    methods_field = 'methods' if language == 'en' else 'metodos'

    label = f"<<table border='0' cellborder='1' cellspacing='0'><tr><td bgcolor='lightgrey'><b>{class_name}</b></td></tr>"

    for attribute in class_data.get(attributes_field, []):
        label += f"<tr><td align='left'>{attribute}</td></tr>"

    for method in class_data.get(methods_field, []):
        label += f"<tr><td align='left'>{method}</td></tr>"

    label += "</table>>"
    return label


def generate_class_diagram(data: Dict[str, Any], language: str = 'pt') -> graphviz.Digraph:
    """
    Gera um diagrama de classes usando Graphviz.

    Args:
        data: Dados para o diagrama
        language: Idioma dos campos ('pt' para português, 'en' para inglês)

    Returns:
        graphviz.Digraph: Objeto do diagrama
    """
    if language == 'en':
        title_field = 'title'
        classes_field, relationships_field = 'classes', 'relationships'
        from_field, to_field, type_field = 'from', 'to', 'type'
        name_field = 'name'
        mult_from_field, mult_to_field = 'multiplicity_from', 'multiplicity_to'
    else:
        title_field = 'titulo'
        classes_field, relationships_field = 'classes', 'relacionamentos'
        from_field, to_field, type_field = 'de', 'para', 'tipo'
        name_field = 'nome'
        mult_from_field, mult_to_field = 'multiplicidade_de', 'multiplicidade_para'

    title = data.get(title_field, 'Diagrama de Classes')
    dot = graphviz.Digraph(comment=title, graph_attr={'rankdir': 'BT'})

    for class_item in data.get(classes_field, []):
        class_name = class_item[name_field]
        label = _build_class_label(class_name, class_item, language)
        dot.node(class_name, label=label, shape='none')

    for rel in data.get(relationships_field, []):
        dot.edge(
            rel[from_field],
            rel[to_field],
            label=rel.get(type_field, ''),
            arrowhead='normal',
            arrowtail='none',
            xlabel=rel.get(mult_from_field, ''),
            ylabel=rel.get(mult_to_field, ''),
        )

    return dot
