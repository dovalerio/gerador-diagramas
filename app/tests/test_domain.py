"""
Testes para domain/models.py — GraphNode, GraphEdge, GraphModel.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from domain.models import GraphNode, GraphEdge, GraphModel


@pytest.fixture
def simple_model():
    model = GraphModel()
    model.nodes['A'] = GraphNode(id='A', label='Alpha', shape='box')
    model.nodes['B'] = GraphNode(id='B', label='Beta',  shape='circle')
    model.nodes['C'] = GraphNode(id='C', label='Gamma', shape='diamond')
    model.edges.append(GraphEdge(id='e1', source='A', target='B', label='goes'))
    model.edges.append(GraphEdge(id='e2', source='B', target='C'))
    return model


def test_get_outgoing_edges(simple_model):
    out = simple_model.get_outgoing_edges('A')
    assert len(out) == 1
    assert out[0].target == 'B'


def test_get_incoming_edges(simple_model):
    inc = simple_model.get_incoming_edges('B')
    assert len(inc) == 1
    assert inc[0].source == 'A'


def test_get_connected_node_ids(simple_model):
    connected = simple_model.get_connected_node_ids('B')
    assert set(connected) == {'A', 'C'}


def test_get_all_edges_for_node(simple_model):
    edges = simple_model.get_all_edges_for_node('B')
    assert len(edges) == 2


def test_node_label_known(simple_model):
    assert simple_model.node_label('A') == 'Alpha'


def test_node_label_unknown(simple_model):
    assert simple_model.node_label('Z') == 'Z'


def test_graph_node_defaults():
    node = GraphNode(id='x', label='X')
    assert node.shape == 'box'
    assert node.description == ''
    assert node.metadata == {}


def test_graph_edge_defaults():
    edge = GraphEdge(id='e0', source='A', target='B')
    assert edge.label == ''
    assert edge.style == 'solid'
    assert edge.metadata == {}
