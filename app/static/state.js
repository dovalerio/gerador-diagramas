/**
 * DiagramState — centralised state for the v2 SVG diagram viewer.
 * Module pattern: exposes only the public API.
 */
const DiagramState = (() => {
  let _selectedNodeId = null;
  let _focusedNodeId  = null;
  let _listeners      = {};

  function _emit(event, payload) {
    (_listeners[event] || []).forEach(fn => fn(payload));
  }

  return {
    on(event, fn) {
      if (!_listeners[event]) _listeners[event] = [];
      _listeners[event].push(fn);
    },
    off(event, fn) {
      _listeners[event] = (_listeners[event] || []).filter(f => f !== fn);
    },

    selectNode(id) {
      if (_selectedNodeId === id) return;
      const prev = _selectedNodeId;
      _selectedNodeId = id;
      _emit('nodeSelected', { id, prev });
    },

    focusNode(id) {
      if (_focusedNodeId === id) return;
      const prev = _focusedNodeId;
      _focusedNodeId = id;
      _emit('nodeFocused', { id, prev });
    },

    get selectedNodeId() { return _selectedNodeId; },
    get focusedNodeId()  { return _focusedNodeId;  },

    clear() {
      const prev = _selectedNodeId;
      _selectedNodeId = null;
      _focusedNodeId  = null;
      if (prev) _emit('nodeSelected', { id: null, prev });
    },
  };
})();
