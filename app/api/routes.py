"""
Rotas da API para geração de diagramas.
"""
import uuid
import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory

from config.settings import UPLOAD_FOLDER, OPENROUTER_API_KEY
from core.diagram_manager import generate_diagram
from core.ai_service import generate_yaml_from_prompt


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
    """
    Serve arquivos de diagrama gerados a partir do diretório de uploads.
    
    Args:
        filename (str): Nome do arquivo a ser servido
        
    Returns:
        Resposta de arquivo
    """
    return send_from_directory(UPLOAD_FOLDER, filename)