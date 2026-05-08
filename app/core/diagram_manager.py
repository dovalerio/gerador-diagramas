"""
Central diagram manager.
"""
import os
import yaml
import graphviz
from typing import Dict, Any, Tuple, Optional

from config.settings import UPLOAD_FOLDER
from core.diagram_generators import DIAGRAM_GENERATORS
from core.language_utils import detect_language, get_diagram_generators


def generate_diagram(yaml_data: str, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Processa o YAML e gera o diagrama correspondente.

    Args:
        yaml_data: Conteúdo YAML como string
        filename: Nome base do arquivo de saída (sem extensão)

    Returns:
        Tupla (url_imagem, descricao_alternativa, mensagem_erro)
    """
    try:
        data = yaml.safe_load(yaml_data)

        language = detect_language(data)
        generators = get_diagram_generators(language)

        if language == 'en':
            if not data or 'diagram' not in data:
                return None, None, "Error: Invalid YAML or missing 'diagram' key."
            diagram_data = data['diagram']
            diagram_type = diagram_data['type']
            diagram_title = diagram_data['title']
            alt_description = diagram_data.get('alternative_description', f'Diagram of type {diagram_type}')
        else:
            if not data or 'diagrama' not in data:
                return None, None, "Erro: YAML inválido ou chave 'diagrama' ausente."
            diagram_data = data['diagrama']
            diagram_type = diagram_data['tipo']
            diagram_title = diagram_data['titulo']
            alt_description = diagram_data.get('descricao_alternativa', f'Diagrama do tipo {diagram_type}')

        diagram_generator = generators.get(diagram_type)
        if not diagram_generator:
            error_msg = (
                f"Diagram type '{diagram_type}' not supported."
                if language == 'en'
                else f"Tipo de diagrama '{diagram_type}' não suportado."
            )
            return None, None, error_msg

        dot = diagram_generator(diagram_data, language)
        if not dot:
            error_msg = "Error generating diagram." if language == 'en' else "Erro ao gerar diagrama."
            return None, None, error_msg

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        output_path = os.path.join(UPLOAD_FOLDER, filename)
        dot.render(output_path, format="png", cleanup=True)

        image_url = f"/static/uploads/{filename}.png"
        return image_url, alt_description, None

    except yaml.YAMLError as e:
        return None, None, f"Erro ao carregar YAML: {e}"
    except graphviz.ExecutableNotFound:
        return None, None, "Erro: Graphviz não está instalado ou não está no PATH."
    except Exception as e:
        return None, None, f"Erro inesperado: {str(e)}"
