// ── Scenario Manager ──────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _codeEditor = null;
    let _usingTextarea = false;
    let _currentStatus = 'idle';
    let _pendingLoopUpdate = false;
    let _loopDebounce = null;

    const PERSIST_KEYS = ['loopMode', 'loopDelay', 'loopRuntime', 'modelCheckEnabled', 'modelCheckConfig'];

    const TEMPLATE_PLACEHOLDER = '# Loading template.launch.py...';

    function editorValue() {
        if (_usingTextarea) return document.getElementById('scenarioTextarea').value;
        return _codeEditor ? _codeEditor.getValue() : '';
    }

    function setEditorValue(v) {
        if (_usingTextarea) { document.getElementById('scenarioTextarea').value = v; return; }
        if (_codeEditor) _codeEditor.setValue(v);
    }

    function initEditor() {
        try {
            _codeEditor = CodeMirror(document.getElementById('codeEditor'), {
                mode: 'python',
                theme: 'monokai',
                lineNumbers: true,
                matchBrackets: true,
                autoCloseBrackets: true,
                indentUnit: 4,
                indentWithTabs: false,
                lineWrapping: true,
                tabSize: 4,
                value: TEMPLATE_PLACEHOLDER
            });
            setTimeout(() => _codeEditor && _codeEditor.refresh(), 150);
        } catch (e) {
            console.warn('CodeMirror init failed, falling back to textarea', e);
            document.querySelector('.code-editor-container').style.display = 'none';
            const ta = document.getElementById('scenarioTextarea');
            ta.style.display = 'block';
            ta.value = TEMPLATE_PLACEHOLDER;
            _usingTextarea = true;
        }
    }

    async function loadTemplate() {
        try {
            const r = await fetch('/api/scenario/template');
            const d = await r.json();
            if (d.success) {
                if (editorValue().trim() === TEMPLATE_PLACEHOLDER.trim() || editorValue().trim() === '') {
                    setEditorValue(d.content);
                }
            } else {
                console.warn('template.launch.py not available:', d.message);
                if (editorValue().trim() === TEMPLATE_PLACEHOLDER.trim()) {
                    setEditorValue('# template.launch.py not found in scenarios directory.\n# Create one or select a scenario from the list above.\n');
                }
            }
        } catch (e) {
            console.warn('Failed to load template:', e);
        }
    }

    // ── localStorage persistence ──────────────────────────────────────────────

    function saveLoopPrefs() {
        PERSIST_KEYS.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            localStorage.setItem('scenario_' + id,
                el.type === 'checkbox' ? el.checked : el.value);
        });
    }

    function restoreLoopPrefs() {
        PERSIST_KEYS.forEach(id => {
            const stored = localStorage.getItem('scenario_' + id);
            if (stored === null) return;
            const el = document.getElementById(id);
            if (!el) return;
            if (el.type === 'checkbox') {
                el.checked = stored === 'true';
            } else {
                el.value = stored;
            }
        });
    }

    // ── Scenarios ─────────────────────────────────────────────────────────────

    async function loadScenarios() {
        try {
            const r = await fetch('/api/scenario/get');
            const d = await r.json();
            window.FuzzyFinder.setScenarios(d.scenarios || []);
        } catch (e) {
            console.error('loadScenarios:', e);
        }
    }

    async function startScenario() {
        const scenario = window.FuzzyFinder.getSelectedScenario();
        if (!scenario) { alert('Select a scenario first.'); return; }

        if (_currentStatus === 'running') {
            if (!confirm('A scenario is running. Halt it and start the selected one?')) return;
            await fetch('/api/scenario/halt', { method: 'POST' });
            await delay(2000);
        }

        const r = await fetch('/api/scenario/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario,
                is_file: true,
                model_check_enabled: document.getElementById('modelCheckEnabled').checked,
                model_check_config: document.getElementById('modelCheckConfig').value
            })
        });
        const result = await r.json();
        if (!result.success) alert(result.message);
    }

    async function restartScenario() {
        const r = await fetch('/api/scenario/restart', { method: 'POST' });
        const result = await r.json();
        if (!result.success) alert(result.message);
    }

    async function haltAll() {
        if (!confirm('Halt all ROS2 processes?')) return;
        const r = await fetch('/api/scenario/halt', { method: 'POST' });
        const result = await r.json();
        if (!result.success) alert(result.message);
    }

    async function runFromEditor() {
        const content = editorValue().trim();
        if (!content) { alert('Editor is empty.'); return; }

        if (_currentStatus === 'running') {
            if (!confirm('A scenario is running. Replace it with the editor content?')) return;
            await fetch('/api/scenario/halt', { method: 'POST' });
            await delay(2000);
        }

        const r = await fetch('/api/scenario/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario: content,
                is_file: false,
                model_check_enabled: document.getElementById('modelCheckEnabled').checked,
                model_check_config: document.getElementById('modelCheckConfig').value
            })
        });
        const result = await r.json();
        if (!result.success) alert(result.message);
    }

    async function saveScenario() {
        const name = document.getElementById('scenarioName').value.trim();
        const content = editorValue().trim();
        if (!name || !content) { alert('Enter scenario name and editor content.'); return; }

        const r = await fetch('/api/scenario/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content })
        });
        const result = await r.json();
        alert(result.message);
        if (result.success) { document.getElementById('scenarioName').value = ''; loadScenarios(); }
    }

    async function copySelected() {
        const scenario = window.FuzzyFinder.getSelectedScenario();
        if (!scenario) { alert('Select a scenario first.'); return; }

        const r = await fetch(`/api/scenario/content/${encodeURIComponent(scenario)}`);
        const result = await r.json();
        if (result.success) {
            setEditorValue(result.content);
        } else {
            alert(result.message || 'Failed to copy scenario.');
        }
    }

    async function toggleLoopMode() {
        _pendingLoopUpdate = false;
        saveLoopPrefs();
        await fetch('/api/scenario/loop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled: document.getElementById('loopMode').checked,
                delay: parseInt(document.getElementById('loopDelay').value) || 0,
                runtime: parseInt(document.getElementById('loopRuntime').value) || 60,
                model_check_enabled: document.getElementById('modelCheckEnabled').checked,
                model_check_config: document.getElementById('modelCheckConfig').value
            })
        });
    }

    function scheduleLoopUpdate() {
        _pendingLoopUpdate = true;
        clearTimeout(_loopDebounce);
        _loopDebounce = setTimeout(toggleLoopMode, 600);
    }

    // ── Status polling ────────────────────────────────────────────────────────

    async function updateStatus() {
        try {
            const r = await fetch('/api/scenario/status');
            const s = await r.json();
            _currentStatus = s.status;

            const ind = document.getElementById('globalStatusIndicator');
            const txt = document.getElementById('globalStatusText');
            if (ind) {
                const indicatorStatus = s.loop_restarting ? 'restarting' : s.status;
                ind.className = `status-indicator status-${indicatorStatus}`;
            }

            let label = s.status.toUpperCase();
            if (s.loop_restarting) label = 'RESTARTING (loop)';
            if (s.scenario && !s.loop_restarting) label += ` — ${s.scenario}`;
            if (s.runtime) label += ` (${Math.round(s.runtime)}s`;
            if (s.runtime && s.loop_mode && !s.loop_restarting) {
                label += ` / ${s.default_runtime}s`;
            }
            if (s.runtime) label += `)`;
            if (s.waiting_for_model_check) label += ' · awaiting model check';
            if (s.loop_mode && !s.loop_restarting) label += ' · looping';
            if (txt) txt.textContent = label;

            // Only sync server-side loop settings if the user isn't actively editing them
            if (!_pendingLoopUpdate) {
                syncCheckbox('loopMode', s.loop_mode);
                syncInput('loopDelay', s.loop_delay);
                syncInput('loopRuntime', s.default_runtime);
                syncCheckbox('modelCheckEnabled', s.model_check_enabled !== false);
                syncInput('modelCheckConfig', s.model_check_config || 'config/default.yaml');
            }

            const startBtn = document.getElementById('startBtn');
            const restartBtn = document.getElementById('restartBtn');
            const runCustomBtn = document.getElementById('runCustomBtn');
            const isRunning = s.status === 'running';
            if (startBtn) startBtn.disabled = isRunning;
            if (restartBtn) restartBtn.disabled = !isRunning;
            if (runCustomBtn) {
                runCustomBtn.textContent = isRunning ? '▶ Replace Running' : '▶ Run from Editor';
                runCustomBtn.className = isRunning ? 'btn-warning' : 'btn-success';
            }
        } catch (e) { /* network */ }
    }

    function syncCheckbox(id, value) {
        const el = document.getElementById(id);
        if (el && el !== document.activeElement) el.checked = value;
    }

    function syncInput(id, value) {
        const el = document.getElementById(id);
        if (el && el !== document.activeElement) el.value = value;
    }

    // ── Log ───────────────────────────────────────────────────────────────────

    let _lastLogContent = '';

    async function updateLog() {
        try {
            const r = await fetch('/api/scenario/output?lines=200');
            const d = await r.json();
            const el = document.getElementById('scenarioLogContainer');
            if (!el) return;
            const text = d.output || '';
            if (text === _lastLogContent) return;
            _lastLogContent = text;
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            const shouldScroll = document.getElementById('autoScrollScenario')?.checked;
            if (shouldScroll || atBottom) {
                el.textContent = text;
                if (shouldScroll) el.scrollTop = el.scrollHeight;
            } else {
                const newText = text.slice(_lastRenderedLength ?? 0);
                if (newText) el.textContent += newText;
            }
            _lastRenderedLength = text.length;
        } catch (e) { /* network */ }
    }

    // ── Positions ─────────────────────────────────────────────────────────────

    async function updateStoredPositions() {
        try {
            const r = await fetch('/api/positions/get');
            const positions = await r.json();
            const el = document.getElementById('storedPositionsInfo');
            if (!el) return;

            const goals = positions.goals || [];
            if (!positions.start && goals.length === 0) {
                el.innerHTML = '<div class="no-stored-positions">No positions stored</div>';
                return;
            }

            let html = '';
            if (positions.start) {
                const { lat, lng, psi } = positions.start;
                html += `<div class="position-item">
                    <strong>🟢 Start</strong><br>
                    ${lat.toFixed(6)}, ${lng.toFixed(6)}&nbsp;|&nbsp;ψ=${(psi||0).toFixed(3)} rad<br>
                    <code>Position(lat_long=(${lat.toFixed(6)}, ${lng.toFixed(6)}), psi=${(psi||0).toFixed(3)})</code>
                </div>`;
            }
            goals.forEach((g, i) => {
                const stopLabel = g.stop ? ' <span style="color:#e67e00">[STOP]</span>' : '';
                html += `<div class="position-item">
                    <strong>🔴 Goal ${i + 1}</strong>${stopLabel}<br>
                    ${g.lat.toFixed(6)}, ${g.lng.toFixed(6)}<br>
                    <code>(${g.lat.toFixed(6)}, ${g.lng.toFixed(6)}, ${g.stop ? 1 : 0})</code>
                </div>`;
            });
            el.innerHTML = html;
        } catch (e) { /* network */ }
    }

    async function applyPositions() {
        const r = await fetch('/api/positions/get');
        const positions = await r.json();
        const goals = positions.goals || [];
        if (!positions.start && goals.length === 0) {
            alert('No stored positions. Use Goal Picker first.');
            return;
        }
        let lines = editorValue().split('\n');
        if (positions.start) {
            const line = `start_position = Position(lat_long=(${positions.start.lat.toFixed(6)}, ${positions.start.lng.toFixed(6)}), psi=${(positions.start.psi||0).toFixed(3)})`;
            const idx = lines.findIndex(l => l.trim().startsWith('start_position = Position('));
            if (idx >= 0) lines[idx] = line; else lines.unshift(line);
        }
        if (goals.length > 0) {
            const items = goals.map(g => `    (${g.lat.toFixed(6)}, ${g.lng.toFixed(6)}, ${g.stop ? 1 : 0})`);
            const block = `goal_positions = [\n${items.join(',\n')}\n]`;
            const start = lines.findIndex(l => l.trim().startsWith('goal_positions = ['));
            if (start >= 0) {
                const end = lines.findIndex((l, i) => i > start && l.trim() === ']');
                lines.splice(start, end >= 0 ? end - start + 1 : 1, ...block.split('\n'));
            } else {
                const afterStart = lines.findIndex(l => l.trim().startsWith('start_position = '));
                const insertAt = afterStart >= 0 ? afterStart + 1 : lines.length;
                lines.splice(insertAt, 0, ...block.split('\n'));
            }
        }
        setEditorValue(lines.join('\n'));
    }

    async function clearPositions() {
        if (!confirm('Clear stored positions?')) return;
        const r = await fetch('/api/positions/clear', { method: 'POST' });
        const result = await r.json();
        if (result.success) updateStoredPositions();
    }

    function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

    // ── Init ──────────────────────────────────────────────────────────────────

    function init() {
        initEditor();
        loadTemplate();
        loadScenarios();
        restoreLoopPrefs();
        updateStatus();
        updateLog();
        updateStoredPositions();

        document.getElementById('startBtn')?.addEventListener('click', startScenario);
        document.getElementById('restartBtn')?.addEventListener('click', restartScenario);
        document.getElementById('haltBtn')?.addEventListener('click', haltAll);
        document.getElementById('runCustomBtn')?.addEventListener('click', runFromEditor);
        document.getElementById('saveBtn')?.addEventListener('click', saveScenario);
        document.getElementById('copySelectedBtn')?.addEventListener('click', copySelected);
        document.getElementById('clearEditorBtn')?.addEventListener('click', () => {
            if (confirm('Reset editor to template?')) loadTemplate();
        });
        document.getElementById('applyPositionsBtn')?.addEventListener('click', applyPositions);
        document.getElementById('clearPositionsBtn')?.addEventListener('click', clearPositions);

        PERSIST_KEYS.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.addEventListener('change', scheduleLoopUpdate);
            el.addEventListener('input', scheduleLoopUpdate);
        });

        setInterval(updateStatus, 1000);
        setInterval(updateLog, 2000);
        setInterval(updateStoredPositions, 5000);
    }

    window.addEventListener('DOMContentLoaded', init);
    window.ScenarioMgr = { editorValue, setEditorValue };
})();
