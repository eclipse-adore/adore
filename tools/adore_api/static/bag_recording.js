// ── Bag File Recording ────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _bagStatus = 'idle';
    let _statusInterval = null;

    async function loadTopics() {
        try {
            const r = await fetch('/api/topic/list');
            const d = await r.json();
            const topics = d.system_topics || [];
            const container = document.getElementById('topicsContainer');
            if (!container) return;

            if (topics.length === 0) {
                container.innerHTML = '<div style="color:#6c757d;text-align:center;padding:8px;">No topics available</div>';
                return;
            }
            container.innerHTML = topics.map(t => `
                <label class="topic-checkbox">
                    <input type="checkbox" value="${t}"> ${t}
                </label>
            `).join('');
        } catch (e) { console.error('loadTopics:', e); }
    }

    function getSelectedTopics() {
        if (document.getElementById('recordAllTopics')?.checked) return [];
        return Array.from(
            document.querySelectorAll('#topicsContainer input[type="checkbox"]:checked')
        ).map(cb => cb.value);
    }

    async function startRecording() {
        const duration = parseInt(document.getElementById('bagDuration')?.value) || null;
        const topics = getSelectedTopics();
        try {
            const r = await fetch('/api/bag/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration: duration || undefined, topics })
            });
            const result = await r.json();
            if (!result.success) alert('Failed to start recording: ' + result.message);
        } catch (e) { alert('Failed to start recording'); }
    }

    async function stopRecording() {
        try {
            const r = await fetch('/api/bag/stop', { method: 'POST' });
            const result = await r.json();
            if (result.success) {
                alert(`Recording saved: ${result.relative_path}`);
                refreshBagList();
            } else {
                alert('Failed to stop recording: ' + result.message);
            }
        } catch (e) { alert('Failed to stop recording'); }
    }

    async function updateBagStatus() {
        try {
            const r = await fetch('/api/bag/status');
            const s = await r.json();
            _bagStatus = s.status || 'idle';

            const ind = document.getElementById('bagStatusIndicator');
            const txt = document.getElementById('bagStatusText');
            if (ind) ind.className = `status-indicator status-${_bagStatus}`;
            if (txt) {
                let label = _bagStatus.toUpperCase();
                if (s.bag_name) label += ` — ${s.bag_name}`;
                if (s.runtime) label += ` (${Math.round(s.runtime)}s)`;
                txt.textContent = label;
            }

            const startBtn = document.getElementById('startBagBtn');
            const stopBtn = document.getElementById('stopBagBtn');
            const isRec = _bagStatus === 'recording';
            if (startBtn) startBtn.disabled = isRec;
            if (stopBtn) stopBtn.disabled = !isRec;
        } catch (e) { /* network */ }
    }

    let _lastBagLog = '';

    async function updateBagLog() {
        try {
            const r = await fetch('/api/bag/output?lines=80');
            const d = await r.json();
            const el = document.getElementById('bagLogContainer');
            if (!el) return;
            const text = d.output || '';
            if (text === _lastBagLog) return;
            _lastBagLog = text;
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            el.textContent = text;
            if (atBottom) el.scrollTop = el.scrollHeight;
        } catch (e) { /* network */ }
    }

    async function refreshBagList() {
        try {
            const r = await fetch('/api/bag/list');
            const d = await r.json();
            const el = document.getElementById('bagRecordingsList');
            if (!el) return;

            if (!d.success || d.bags.length === 0) {
                el.innerHTML = '<div class="no-running-nodes">No recordings found</div>';
                return;
            }
            el.innerHTML = d.bags.map(b => `
                <div class="bag-item">
                    <strong>${b.name}</strong>
                    <span class="bag-meta">${b.created} &nbsp;·&nbsp; ${b.size_mb.toFixed(2)} MB</span>
                    <code class="bag-path">${b.relative_path}</code>
                </div>
            `).join('');
        } catch (e) { console.error('refreshBagList:', e); }
    }

    function init() {
        document.getElementById('recordAllTopics')?.addEventListener('change', e => {
            const sel = document.getElementById('topicsSelectionContainer');
            if (sel) sel.style.display = e.target.checked ? 'none' : 'block';
        });
        document.getElementById('refreshTopicsBtn')?.addEventListener('click', loadTopics);
        document.getElementById('startBagBtn')?.addEventListener('click', startRecording);
        document.getElementById('stopBagBtn')?.addEventListener('click', stopRecording);
        document.getElementById('refreshBagListBtn')?.addEventListener('click', refreshBagList);

        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'bag-recording') {
                loadTopics();
                refreshBagList();
                if (!_statusInterval) {
                    updateBagStatus();
                    updateBagLog();
                    _statusInterval = setInterval(() => { updateBagStatus(); updateBagLog(); }, 2000);
                }
            } else {
                if (_statusInterval) { clearInterval(_statusInterval); _statusInterval = null; }
            }
        });

        // Always poll status (needed for button states even when tab is inactive)
        updateBagStatus();
        setInterval(updateBagStatus, 3000);
    }

    window.addEventListener('DOMContentLoaded', init);
})();
