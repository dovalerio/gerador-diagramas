/**
 * NodeTree — renders an accessible tree panel from SVG node data.
 * Supports arrow-key navigation and syncs selection with DiagramState.
 */
const NodeTree = (() => {
  let _container = null;
  let _items     = [];   // [{id, label, connectedTo}]

  function _getItems() { return _items; }

  function _itemEl(id) {
    return _container && _container.querySelector(`[data-node-id="${CSS.escape(id)}"]`);
  }

  function _setSelected(id) {
    if (!_container) return;
    _container.querySelectorAll('[role=treeitem]').forEach(el => {
      const sel = el.dataset.nodeId === id;
      el.setAttribute('aria-selected', sel ? 'true' : 'false');
      el.setAttribute('tabindex', sel ? '0' : '-1');
    });
  }

  function _buildItem(item) {
    const li = document.createElement('li');
    li.setAttribute('role', 'treeitem');
    li.setAttribute('aria-selected', 'false');
    li.setAttribute('tabindex', '-1');
    li.dataset.nodeId = item.id;
    li.textContent = item.label;
    return li;
  }

  function _onKeydown(e) {
    const focused = document.activeElement;
    if (!focused || focused.getAttribute('role') !== 'treeitem') return;

    const idx = _items.findIndex(n => n.id === focused.dataset.nodeId);
    if (idx === -1) return;

    let next = null;
    if (e.key === 'ArrowDown') { next = _items[idx + 1]; e.preventDefault(); }
    if (e.key === 'ArrowUp')   { next = _items[idx - 1]; e.preventDefault(); }
    if (e.key === 'Home')      { next = _items[0];       e.preventDefault(); }
    if (e.key === 'End')       { next = _items[_items.length - 1]; e.preventDefault(); }

    if (next) {
      const el = _itemEl(next.id);
      if (el) { el.focus(); DiagramState.focusNode(next.id); }
    }

    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      DiagramState.selectNode(focused.dataset.nodeId);
    }
  }

  return {
    mount(containerEl) {
      _container = containerEl;
      _container.addEventListener('keydown', _onKeydown);

      // Sync selection from state
      DiagramState.on('nodeSelected', ({ id }) => _setSelected(id));
      DiagramState.on('nodeFocused',  ({ id }) => {
        const el = _itemEl(id);
        if (el) el.focus();
      });

      _container.addEventListener('click', e => {
        const li = e.target.closest('[role=treeitem]');
        if (li) DiagramState.selectNode(li.dataset.nodeId);
      });
    },

    render(svgContainer) {
      if (!_container) return;
      _items = [];

      svgContainer.querySelectorAll('g[data-node-id]').forEach(g => {
        _items.push({
          id:          g.dataset.nodeId,
          label:       g.getAttribute('aria-label') || g.dataset.nodeId,
          connectedTo: (g.dataset.connectedTo || '').split(' ').filter(Boolean),
        });
      });

      const ul = document.createElement('ul');
      ul.setAttribute('role', 'tree');
      ul.setAttribute('aria-label', 'Nós do diagrama');
      _items.forEach((item, i) => {
        const li = _buildItem(item);
        if (i === 0) li.setAttribute('tabindex', '0');
        ul.appendChild(li);
      });

      _container.innerHTML = '';
      _container.appendChild(ul);
    },
  };
})();
