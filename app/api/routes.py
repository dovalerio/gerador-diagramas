"""
Rotas da API para geração de diagramas.
v1: YAML → PNG (existing flow, unchanged)
v2: Mermaid or YAML → SVG (new accessible pipeline)
"""
import uuid
import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory

from config.settings import UPLOAD_FOLDER, OPENROUTER_API_KEY
from core.diagram_manager import generate_diagram
from core.ai_service import generate_yaml_from_prompt
from services.diagram_service import DiagramService
from llm.client import LLMClient
from llm.prompt_builder import build_mermaid_prompt
from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

_diagram_service = DiagramService()


api_bp = Blueprint('api', __name__)


@api_bp.route('/')
def index():
    """
    Renderiza a página principal da aplicação.
    
    Returns:
        HTML template renderizado
    """
    return render_template('index.html')


@api_bp.route('/generate_diagram', methods=['POST'])
def generate_diagram_route():
    """
    Gera um diagrama a partir de dados YAML.
    
    Formato JSON da requisição:
        {
            "yaml_data": "String YAML para geração do diagrama"
        }
    
    Returns:
        Resposta JSON com caminho da imagem e descrição alternativa, ou erro
    """
    try:
        yaml_data = request.json['yaml_data']
        if not yaml_data or not yaml_data.strip():
            return jsonify({'error': 'Nenhum dado YAML fornecido'}), 400
            
        filename = str(uuid.uuid4())  # Identificador único para o arquivo
        
        image_path, alt_description, error = generate_diagram(yaml_data, filename)

        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'image_path': image_path,
            'alternative_description': alt_description
        })
    except KeyError:
        return jsonify({'error': 'Campo yaml_data ausente na requisição'}), 400
    except Exception as e:
        return jsonify({'error': f"Erro ao processar requisição: {str(e)}"}), 500


@api_bp.route('/generate_yaml', methods=['POST'])
def generate_yaml_route():
    """
    Gera YAML a partir de descrição textual usando IA.
    
    Formato JSON da requisição:
        {
            "prompt": "Descrição do diagrama desejado"
        }
    
    Returns:
        Resposta JSON com YAML gerado, ou erro
    """
    try:
        # Verificar se a chave API está disponível
        if not OPENROUTER_API_KEY:
            return jsonify({'error': 'Chave da API OpenRouter não está configurada. Recursos de IA estão indisponíveis.'}), 503
            
        prompt = request.json['prompt']
        if not prompt or not prompt.strip():
            return jsonify({'error': 'Nenhum prompt fornecido'}), 400
            
        yaml_content = generate_yaml_from_prompt(prompt)
        return jsonify({'yaml': yaml_content})
        
    except KeyError:
        return jsonify({'error': 'Campo prompt ausente na requisição'}), 400
    except Exception as e:
        return jsonify({'error': f"Erro ao processar requisição: {str(e)}"}), 500


@api_bp.route('/static/uploads/<filename>')
def serve_diagram_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ── API v2 ────────────────────────────────────────────────────────────────────

@api_bp.route('/api/v2/render', methods=['POST'])
def v2_render():
    """
    Render Mermaid or YAML source to accessible SVG.

    Request JSON: { "source": "<mermaid or yaml string>" }
    Response JSON: { "svg": "...", "title": "...", "alt": "..." }
    """
    body = request.get_json(silent=True) or {}
    source = body.get('source', '').strip()
    if not source:
        return jsonify({'error': 'Field "source" is required and must not be empty'}), 400

    try:
        result = _diagram_service.generate(source)
        return jsonify({'svg': result.svg, 'title': result.title, 'alt': result.alt})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': f'Rendering failed: {exc}'}), 500


@api_bp.route('/api/v2/generate', methods=['POST'])
def v2_generate():
    """
    Generate Mermaid from a natural-language prompt, then render to SVG.

    Request JSON: { "prompt": "<description>" }
    Response JSON: { "mermaid": "...", "svg": "...", "title": "...", "alt": "..." }
    """
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'OPENROUTER_API_KEY is not configured'}), 503

    body = request.get_json(silent=True) or {}
    prompt = body.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Field "prompt" is required and must not be empty'}), 400

    try:
        llm = LLMClient(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            model=OPENROUTER_MODEL,
        )
        system_p, user_p = build_mermaid_prompt(prompt)
        mermaid_source = llm.complete(system_p, user_p).strip()

        result = _diagram_service.generate(mermaid_source)
        return jsonify({
            'mermaid': mermaid_source,
            'svg': result.svg,
            'title': result.title,
            'alt': result.alt,
        })
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': f'Generation failed: {exc}'}), 500