"""
Testes de integração para as rotas Flask.
"""
import json
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('OPENROUTER_API_KEY', 'test-key')
os.environ.setdefault('SECRET_KEY', 'test-secret')

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ── Página principal ──────────────────────────────────────────────────────────

def test_index_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


# ── /generate_diagram ─────────────────────────────────────────────────────────

VALID_YAML = """
diagrama:
  tipo: arquitetura
  titulo: Teste
  descricao_alternativa: Diagrama de teste
  usuarios:
    - nome: Usuario
  servicos:
    - nome: Servico
  conexoes:
    - de: Usuario
      para: Servico
      evento: HTTP
"""

INVALID_YAML = "{ isso: não: é: yaml: válido"


def test_generate_diagram_missing_yaml_data(client):
    response = client.post('/generate_diagram',
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400


def test_generate_diagram_empty_yaml(client):
    response = client.post('/generate_diagram',
                           data=json.dumps({'yaml_data': '   '}),
                           content_type='application/json')
    assert response.status_code == 400


def test_generate_diagram_invalid_yaml(client):
    response = client.post('/generate_diagram',
                           data=json.dumps({'yaml_data': INVALID_YAML}),
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_generate_diagram_unsupported_type(client):
    yaml_data = """
diagrama:
  tipo: tipo_inexistente
  titulo: Teste
"""
    response = client.post('/generate_diagram',
                           data=json.dumps({'yaml_data': yaml_data}),
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_generate_diagram_success(client):
    with patch('api.routes.generate_diagram') as mock_gen:
        mock_gen.return_value = ('/static/uploads/test.png', 'Diagrama de teste', None)
        response = client.post('/generate_diagram',
                               data=json.dumps({'yaml_data': VALID_YAML}),
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert 'image_path' in data
        assert 'alternative_description' in data


# ── /generate_yaml ────────────────────────────────────────────────────────────

def test_generate_yaml_missing_key(client):
    response = client.post('/generate_yaml',
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400


def test_generate_yaml_empty_prompt(client):
    response = client.post('/generate_yaml',
                           data=json.dumps({'prompt': '  '}),
                           content_type='application/json')
    assert response.status_code == 400


def test_generate_yaml_no_api_key(client):
    with patch('api.routes.OPENROUTER_API_KEY', None):
        response = client.post('/generate_yaml',
                               data=json.dumps({'prompt': 'crie um diagrama'}),
                               content_type='application/json')
        assert response.status_code == 503


def test_generate_yaml_success(client):
    with patch('api.routes.generate_yaml_from_prompt') as mock_ai:
        mock_ai.return_value = "diagrama:\n  tipo: arquitetura\n  titulo: Teste"
        response = client.post('/generate_yaml',
                               data=json.dumps({'prompt': 'crie um diagrama de arquitetura'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert 'yaml' in data
