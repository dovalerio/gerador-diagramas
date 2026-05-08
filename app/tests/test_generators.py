"""
Testes unitários para os geradores de diagrama.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.diagram_generators.architecture_diagram import generate_architecture_diagram
from core.diagram_generators.class_diagram import generate_class_diagram
from core.diagram_generators.sequence_diagram import generate_sequence_diagram
from core.diagram_generators.use_case_diagram import generate_use_case_diagram
from core.diagram_generators.component_diagram import generate_component_diagram
from core.diagram_generators.deployment_diagram import generate_deployment_diagram


# ── Arquitetura ──────────────────────────────────────────────────────────────

ARCHITECTURE_PT = {
    'titulo': 'Sistema E-commerce',
    'usuarios': [{'nome': 'Cliente'}],
    'servicos': [{'nome': 'Frontend'}, {'nome': 'API'}],
    'conexoes': [{'de': 'Cliente', 'para': 'Frontend', 'evento': 'HTTP'}],
}

ARCHITECTURE_EN = {
    'title': 'E-commerce System',
    'users': [{'name': 'Customer'}],
    'services': [{'name': 'Frontend'}, {'name': 'API'}],
    'connections': [{'from': 'Customer', 'to': 'Frontend', 'event': 'HTTP'}],
}


def test_architecture_pt():
    dot = generate_architecture_diagram(ARCHITECTURE_PT, language='pt')
    src = dot.source
    assert 'Cliente' in src
    assert 'Frontend' in src
    assert 'API' in src


def test_architecture_en():
    dot = generate_architecture_diagram(ARCHITECTURE_EN, language='en')
    src = dot.source
    assert 'Customer' in src
    assert 'Frontend' in src


# ── Classes ───────────────────────────────────────────────────────────────────

CLASS_PT = {
    'titulo': 'Diagrama de Classes',
    'classes': [
        {'nome': 'Pedido', 'atributos': ['int id'], 'metodos': ['confirmar()']},
        {'nome': 'Item', 'atributos': ['str nome'], 'metodos': []},
    ],
    'relacionamentos': [{'de': 'Pedido', 'para': 'Item', 'tipo': 'associação'}],
}

CLASS_EN = {
    'title': 'Class Diagram',
    'classes': [
        {'name': 'Order', 'attributes': ['int id'], 'methods': ['confirm()']},
        {'name': 'Item', 'attributes': ['str name'], 'methods': []},
    ],
    'relationships': [{'from': 'Order', 'to': 'Item', 'type': 'association'}],
}


def test_class_diagram_pt():
    dot = generate_class_diagram(CLASS_PT, language='pt')
    src = dot.source
    assert 'Pedido' in src
    assert 'Item' in src


def test_class_diagram_en():
    dot = generate_class_diagram(CLASS_EN, language='en')
    src = dot.source
    assert 'Order' in src
    assert 'Item' in src


# ── Sequência ─────────────────────────────────────────────────────────────────

SEQUENCE_PT = {
    'titulo': 'Login',
    'objetos': [{'nome': 'Usuário'}, {'nome': 'Sistema'}],
    'mensagens': [{'de': 'Usuário', 'para': 'Sistema', 'mensagem': 'login()'}],
}

SEQUENCE_EN = {
    'title': 'Login',
    'objects': [{'name': 'User'}, {'name': 'System'}],
    'messages': [{'from': 'User', 'to': 'System', 'message': 'login()'}],
}


def test_sequence_diagram_pt():
    dot = generate_sequence_diagram(SEQUENCE_PT, language='pt')
    src = dot.source
    assert 'Usuário' in src
    assert 'Sistema' in src


def test_sequence_diagram_en():
    dot = generate_sequence_diagram(SEQUENCE_EN, language='en')
    src = dot.source
    assert 'User' in src
    assert 'System' in src


# ── Casos de Uso ──────────────────────────────────────────────────────────────

USE_CASE_PT = {
    'titulo': 'Reserva',
    'atores': [{'nome': 'Cliente'}],
    'casos_de_uso': [{'nome': 'Reservar Mesa'}],
    'relacionamentos': [{'de': 'Cliente', 'para': 'Reservar Mesa', 'tipo': 'associação'}],
}

USE_CASE_EN = {
    'title': 'Reservation',
    'actors': [{'name': 'Customer'}],
    'use_cases': [{'name': 'Book Table'}],
    'relationships': [{'from': 'Customer', 'to': 'Book Table', 'type': 'association'}],
}


def test_use_case_diagram_pt():
    dot = generate_use_case_diagram(USE_CASE_PT, language='pt')
    src = dot.source
    assert 'Cliente' in src
    assert 'Reservar Mesa' in src


def test_use_case_diagram_en():
    dot = generate_use_case_diagram(USE_CASE_EN, language='en')
    src = dot.source
    assert 'Customer' in src
    assert 'Book Table' in src


# ── Componentes ───────────────────────────────────────────────────────────────

COMPONENT_PT = {
    'titulo': 'Componentes',
    'componentes': [{'nome': 'Frontend'}, {'nome': 'Backend'}],
    'conexoes': [{'de': 'Frontend', 'para': 'Backend', 'evento': 'REST'}],
}


def test_component_diagram_pt():
    dot = generate_component_diagram(COMPONENT_PT, language='pt')
    src = dot.source
    assert 'Frontend' in src
    assert 'Backend' in src


# ── Implantação ───────────────────────────────────────────────────────────────

DEPLOYMENT_PT = {
    'titulo': 'Implantação',
    'nos': [{'nome': 'Servidor Web'}, {'nome': 'Banco de Dados'}],
    'conexoes': [{'de': 'Servidor Web', 'para': 'Banco de Dados', 'evento': 'SQL'}],
}


def test_deployment_diagram_pt():
    dot = generate_deployment_diagram(DEPLOYMENT_PT, language='pt')
    src = dot.source
    assert 'Servidor Web' in src
    assert 'Banco de Dados' in src
