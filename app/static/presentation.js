/**
 * PresentationMode — handles SVG display, node highlighting,
 * keyboard navigation within the SVG, and sync with NodeTree.
 */
const PresentationMode = (() => {
  let _svgContainer = null;

  const HIGHLIGHT_FILL   = '#DBEAFE';
  const HIGHLIGHT_STROKE = '#1D4ED8';
  const EDGE_HIGHLIGHT   = '#1D4ED8';

  function _getNodeEl(id) {
    return _svgContainer && _svgContainer.querySelector(`g[data-node-id="${CSS.escape(id)}"]`);
  }

  function _clearHighlights() {
    if (!_svgContainer) return;
    _svgContainer.querySelectorAll('rect, ellipse, polygon, circle').forEach(el => {
      el.removeAttribute('data-hl-fill');
      el.removeAttribute('data-hl-stroke');
      if (el.hasAttribute('data-orig-fill'))   el.setAttribute('fill',   el.dataset.origFill);
      if (el.hasAttribute('data-orig-stroke')) el.setAttribute('stroke', el.dataset.origStroke);
    });
    _svgContainer.querySelectorAll('path[data-edge-highlight]').forEach(p => {
      p.setAttribute('stroke', p.dataset.origStroke || '#6B7280');
      delete p.dataset.edgeHighlight;
    });
  }

  function _highlightNode(nodeEl) {
    nodeEl.querySelectorAll('rect, ellipse, polygon').forEach(shape => {
      if (!shape.hasAttribute('data-orig-fill'))
        shape.dataset.origFill = shape.getAttribute('fill') || '';
      if (!shape.hasAttribute('data-orig-stroke'))
        shape.dataset.origStroke = shape.getAttribute('stroke') || '';
      shape.setAttribute('fill',   HIGHLIGHT_FILL);
      shape.setAttribute('stroke', HIGHLIGHT_STROKE);
    });
  }

  function _highlightEdges(nodeId) {
    if (!_svgContainer) return;
    _svgContainer.querySelectorAll('g[data-edge-id]').forEach(g => {
      const lbl = g.getAttribute('aria-label') || '';
      // aria-label contains node labels, not IDs — check data attributes
      // edges do not have source/target as data attrs, so we check connected list
    });

    const nodeEl = _getNodeEl(nodeId);
    if (!nodeEl) return;
    const connected = (nodeEl.dataset.connectedTo || '').split(' ').filter(Boolean);

    _svgContainer.querySelectorAll('g[data-edge-id] path').forEach(path => {
      const g = path.closest('g[data-edge-id]');
      if (!g) return;
      // highlight if this edge connects to the selected node
      // The aria-label on the edge group contains "from X to Y"
      const lbl = g.getAttribute('aria-label') || '';
      const nodeLabel = nodeEl.getAttribute('aria-label') || nodeId;
      if (lbl.includes(nodeLabel)) {
        if (!path.hasAttribute('data-orig-stroke'))
          path.dataset.origStroke = path.getAttribute('stroke') || '#6B7280';
        path.setAttribute('stroke', EDGE_HIGHLIGHT);
        g.dataset.edgeHighlight = '1';
      }
    });
  }

  function _applySelection(id) {
    _clearHighlights();
    if (!id) return;
    const el = _getNodeEl(id);
    if (el) {
      _highlightNode(el);
      _highlightEdges(id);
    }
  }

  function _onKeydown(e) {
    const target = e.target.closest('g[data-node-id]');
    if (!target) return;

    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      DiagramState.selectNode(target.dataset.nodeId);
      const label = target.getAttribute('aria-label') || target.dataset.nodeId;
      const connected = (target.dataset.connectedTo || '').split(' ').filter(Boolean);
      const connMsg = connected.length
        ? `Conectado a: ${connected.join(', ')}`
        : 'Sem conexões';
      A11y.announce(`${label} selecionado. ${connMsg}`);
      return;
    }

    // Arrow navigation: move to first connected node
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const connected = (target.dataset.connectedTo || '').split(' ').filter(Boolean);
      if (connected.length) {
        const nextEl = _getNodeEl(connected[0]);
        if (nextEl) { nextEl.focus(); DiagramState.focusNode(connected[0]); }
      }
    }

    if (e.key === 'Escape') {
      DiagramState.clear();
      A11y.announce('Seleção limpa');
    }
  }

  return {
    mount(containerEl) {
      _svgContainer = containerEl;

      DiagramState.on('nodeSelected', ({ id }) => _applySelection(id));

      _svgContainer.addEventListener('click', e => {
        const g = e.target.closest('g[data-node-id]');
        if (g) {
          DiagramState.selectNode(g.dataset.nodeId);
          const label = g.getAttribute('aria-label') || g.dataset.nodeId;
          A11y.announce(`${label} selecionado`);
        } else {
          DiagramState.clear();
        }
      });

      _svgContainer.addEventListener('keydown', _onKeydown);
    },

    load(svgString) {
      if (!_svgContainer) return;
      DiagramState.clear();
      _svgContainer.innerHTML = svgString;

      // Make every node group focusable
      _svgContainer.querySelectorAll('g[data-node-id]').forEach((g, i) => {
        g.setAttribute('tabindex', i === 0 ? '0' : '-1');
      });
    },
  };
})();
