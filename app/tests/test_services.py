"""
Testes para DiagramService — pipeline completo (parsers → layout → SVG).
Os testes que chamam o layout engine requerem Graphviz no PATH e são
automaticamente ignorados quando `dot` não está disponível.
"""
import shutil
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.diagram_service import DiagramService, _is_mermaid

# Skip layout/render tests when Graphviz is not installed
_GV_AVAILABLE = shutil.which('dot') is not None
requires_gv = pytest.mark.skipif(not _GV_AVAILABLE, reason='Graphviz not in PATH')


# ── _is_mermaid heuristic ─────────────────────────────────────────────────────

def test_is_mermaid_flowchart():
    assert _is_mermaid('flowchart LR\n  A --> B') is True

def test_is_mermaid_graph():
    assert _is_mermaid('graph TD\n  A --> B') is True

def test_is_mermaid_sequence():
    assert _is_mermaid('sequenceDiagram\n  A->>B: hi') is True

def test_is_mermaid_yaml():
    assert _is_mermaid('diagrama:\n  tipo: arquitetura') is False


# ── DiagramService.generate ───────────────────────────────────────────────────

SIMPLE_MERMAID = "flowchart LR\n  A[Alpha] --> B[Beta]\n"

SIMPLE_YAML = """
diagrama:
  tipo: arquitetura
  titulo: Svc Test
  usuarios:
    - nome: User
  servicos:
    - nome: App
  conexoes:
    - de: User
      para: App
      evento: HTTP
"""


@pytest.fixture
def service():
    return DiagramService()


@requires_gv
def test_generate_mermaid_returns_svg(service):
    result = service.generate(SIMPLE_MERMAID)
    assert result.svg.startswith('<svg')
    assert '</svg>' in result.svg


@requires_gv
def test_generate_mermaid_svg_contains_nodes(service):
    result = service.generate(SIMPLE_MERMAID)
    assert 'data-node-id' in result.svg


@requires_gv
def test_generate_yaml_returns_svg(service):
    result = service.generate(SIMPLE_YAML)
    assert result.svg.startswith('<svg')


@requires_gv
def test_generate_yaml_title(service):
    result = service.generate(SIMPLE_YAML)
    assert result.title == 'Svc Test'


def test_generate_empty_raises(service):
    with pytest.raises(ValueError):
        service.generate('   ')


def test_generate_invalid_mermaid_type_raises(service):
    with pytest.raises(ValueError):
        service.generate('gantt\n  title x\n')


@requires_gv
def test_svg_has_aria_label(service):
    result = service.generate(SIMPLE_MERMAID)
    assert 'aria-label' in result.svg


@requires_gv
def test_svg_node_has_role_button(service):
    result = service.generate(SIMPLE_MERMAID)
    assert 'role="button"' in result.svg
