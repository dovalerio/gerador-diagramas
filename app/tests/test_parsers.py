"""
Testes para os parsers Mermaid e YAML.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.mermaid.parser import parse_mermaid
from parsers.yaml_parser.adapters import yaml_to_graph


# ── Mermaid flowchart ─────────────────────────────────────────────────────────

FLOWCHART = """\
flowchart LR
  A[Cliente] --> B[API]
  B -->|SQL| C[(Banco)]
  B --> D{Valido?}
"""

def test_flowchart_node_count():
    model = parse_mermaid(FLOWCHART)
    assert len(model.nodes) == 4

def test_flowchart_edge_count():
    model = parse_mermaid(FLOWCHART)
    assert len(model.edges) == 3

def test_flowchart_edge_label():
    model = parse_mermaid(FLOWCHART)
    labeled = [e for e in model.edges if e.label == 'SQL']
    assert len(labeled) == 1

def test_flowchart_diamond_shape():
    model = parse_mermaid(FLOWCHART)
    assert model.nodes.get('D') is not None
    assert model.nodes['D'].shape == 'diamond'

def test_flowchart_cylinder_shape():
    model = parse_mermaid(FLOWCHART)
    assert model.nodes.get('C') is not None
    assert model.nodes['C'].shape == 'cylinder'

def test_flowchart_type_metadata():
    model = parse_mermaid(FLOWCHART)
    assert model.metadata.get('type') == 'flowchart'


# ── Mermaid sequenceDiagram ───────────────────────────────────────────────────

SEQUENCE = """\
sequenceDiagram
  participant Alice
  participant Bob
  Alice->>Bob: Olá
  Bob-->>Alice: Oi
"""

def test_sequence_participants():
    model = parse_mermaid(SEQUENCE)
    assert 'Alice' in model.nodes
    assert 'Bob' in model.nodes

def test_sequence_message_count():
    model = parse_mermaid(SEQUENCE)
    assert len(model.edges) == 2

def test_sequence_reply_is_dashed():
    model = parse_mermaid(SEQUENCE)
    dashed = [e for e in model.edges if e.style == 'dashed']
    assert len(dashed) >= 1


# ── Mermaid classDiagram ──────────────────────────────────────────────────────

CLASS_DIAG = """\
classDiagram
  class Animal {
    +name: str
    +speak()
  }
  class Dog
  Animal <|-- Dog : extends
"""

def test_class_nodes():
    model = parse_mermaid(CLASS_DIAG)
    assert 'Animal' in model.nodes
    assert 'Dog' in model.nodes

def test_class_inheritance_edge():
    model = parse_mermaid(CLASS_DIAG)
    assert len(model.edges) >= 1
    assert model.edges[0].style == 'solid'


# ── Unsupported Mermaid type ──────────────────────────────────────────────────

def test_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_mermaid("gantt\n  title Plan\n")


# ── YAML adapter ──────────────────────────────────────────────────────────────

ARCH_YAML = """
diagrama:
  tipo: arquitetura
  titulo: Teste
  usuarios:
    - nome: Usuario
  servicos:
    - nome: API
    - nome: DB
  conexoes:
    - de: Usuario
      para: API
      evento: HTTP
    - de: API
      para: DB
      evento: SQL
"""

def test_yaml_arch_nodes():
    model = yaml_to_graph(ARCH_YAML)
    assert len(model.nodes) == 3

def test_yaml_arch_edges():
    model = yaml_to_graph(ARCH_YAML)
    assert len(model.edges) == 2

def test_yaml_arch_title():
    model = yaml_to_graph(ARCH_YAML)
    assert model.metadata['title'] == 'Teste'

def test_yaml_invalid_type():
    with pytest.raises(ValueError):
        yaml_to_graph("diagrama:\n  tipo: xyzzy\n")

def test_yaml_missing_key():
    with pytest.raises(ValueError):
        yaml_to_graph("foo: bar\n")
