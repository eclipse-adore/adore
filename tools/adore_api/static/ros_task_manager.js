// ── ROS Task Manager ──────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _selectedNode = null;
    let _refreshInterval = null;

    function setSelectedNode(node) {
        _selectedNode = node;
        const display = document.getElementById('selectedNodeDisplay');
        const haltBtn = document.getElementById('haltNodeBtn');
        if (display) display.value = node || '';
        if (haltBtn) haltBtn.disabled = !node;

        document.querySelectorAll('.node-list-item').forEach(el => {
            el.classList.toggle('node-selected', el.dataset.node === node);
        });
    }

    async function fetchNodes() {
        try {
            const r = await fetch('/api/ros2/nodes/running');
            const d = await r.json();
            renderNodes(d.running_nodes || []);
            const countEl = document.getElementById('ros-node-count');
            const updateEl = document.getElementById('ros-node-last-update');
            if (countEl) countEl.textContent = d.count || 0;
            if (updateEl) updateEl.textContent = 'updated ' + new Date().toLocaleTimeString();
        } catch (e) {
            const el = document.getElementById('ros-node-list');
            if (el) el.innerHTML = '<div class="no-running-nodes">Failed to load nodes</div>';
        }
    }

    function renderNodes(nodes) {
        const el = document.getElementById('ros-node-list');
        if (!el) return;

        if (nodes.length === 0) {
            el.innerHTML = '<div class="no-running-nodes">No running nodes</div>';
            return;
        }

        el.innerHTML = nodes.map(n => `
            <div class="node-list-item${n === _selectedNode ? ' node-selected' : ''}"
                 data-node="${n}" title="${n}">
                <span class="node-dot"></span>
                <span class="node-name">${n}</span>
            </div>
        `).join('');

        el.querySelectorAll('.node-list-item').forEach(item => {
            item.addEventListener('click', () => setSelectedNode(item.dataset.node));
        });
    }

    async function haltNode() {
        if (!_selectedNode) return;
        if (!confirm(`Kill node: ${_selectedNode}?`)) return;

        try {
            const r = await fetch('/api/scenario/halt', { method: 'POST' });
            await fetchNodes();
            setSelectedNode(null);
        } catch (e) {
            alert('Failed to halt node: ' + e.message);
        }
    }

    async function killAllNodes() {
        if (!confirm('Kill all running ROS2 nodes?')) return;
        try {
            await fetch('/api/scenario/halt', { method: 'POST' });
            await delay(500);
            await fetchNodes();
            setSelectedNode(null);
        } catch (e) {
            alert('Failed to kill nodes: ' + e.message);
        }
    }

    function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

    function init() {
        document.getElementById('refreshNodesBtn')?.addEventListener('click', fetchNodes);
        document.getElementById('killAllNodesBtn')?.addEventListener('click', killAllNodes);
        document.getElementById('haltNodeBtn')?.addEventListener('click', haltNode);

        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'ros-task-manager') {
                fetchNodes();
                if (!_refreshInterval) _refreshInterval = setInterval(fetchNodes, 5000);
            } else {
                if (_refreshInterval) { clearInterval(_refreshInterval); _refreshInterval = null; }
            }
        });
    }

    window.addEventListener('DOMContentLoaded', init);
})();
