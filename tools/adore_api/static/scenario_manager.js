// ── Scenario Manager ──────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _codeEditor = null;
    let _usingTextarea = false;
    let _currentStatus = 'idle';
    let _isEditingLoop = false;
    let _loopDebounce = null;

    const DEFAULT_LAUNCH = `from launch import LaunchDescription
import os, sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
from scenario_helpers.simulated_vehicle import create_simulated_vehicle_nodes, Position
from scenario_helpers.visualizer import create_visualization_nodes

start_position = Position(lat_long=(52.314562, 10.560474), psi=0.0)
goal_position  = Position(lat_long=(52.313533, 10.560554))

def generate_launch_description():
    launch_file_dir  = os.path.dirname(os.path.realpath(__file__))
    map_image_folder = os.path.abspath(os.path.join(launch_file_dir, "../assets/maps/"))
    map_folder       = os.path.abspath(os.path.join(launch_file_dir, "../assets/tracks/"))
    vehicle_param    = os.path.abspath(os.path.join(launch_file_dir, "../assets/vehicle_params/"))
    map_file         = map_folder + "/de_bs_borders_wfs.r2sr"
    vehicle_model_file = vehicle_param + "/NGC.json"

    return LaunchDescription([
        *create_visualization_nodes(
            whitelist=["ego_vehicle"],
            asset_folder=map_image_folder,
            use_center_ego=True
        ),
        *create_simulated_vehicle_nodes(
            namespace="ego_vehicle",
            start_position=start_position,
            goal_position=goal_position,
            map_file=map_file,
            model_file=vehicle_model_file,
            controllable=True,
            optinlc_route_following=True,
            v2x_id=0, vehicle_id=0,
            controller=1, debug=False, composable=False
        )
    ])
`;

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
                value: DEFAULT_LAUNCH
            });
            setTimeout(() => _codeEditor && _codeEditor.refresh(), 150);
        } catch (e) {
            console.warn('CodeMirror init failed, falling back to textarea', e);
            document.querySelector('.code-editor-container').style.display = 'none';
            const ta = document.getElementById('scenarioTextarea');
            ta.style.display = 'block';
            ta.value = DEFAULT_LAUNCH;
            _usingTextarea = true;
        }
    }

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
        if (_isEditingLoop) return;
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

    async function updateStatus() {
        try {
            const r = await fetch('/api/scenario/status');
            const s = await r.json();
            _currentStatus = s.status;

            const ind = document.getElementById('globalStatusIndicator');
            const txt = document.getElementById('globalStatusText');
            if (ind) ind.className = `status-indicator status-${s.status}`;
            let label = s.status.toUpperCase();
            if (s.scenario) label += ` — ${s.scenario}`;
            if (s.runtime) label += ` (${Math.round(s.runtime)}s)`;
            if (s.waiting_for_model_check) label += ' · awaiting model check';
            if (txt) txt.textContent = label;

            if (!_isEditingLoop) {
                document.getElementById('loopMode').checked = s.loop_mode;
                document.getElementById('loopDelay').value = s.loop_delay;
                document.getElementById('loopRuntime').value = s.default_runtime;
                document.getElementById('modelCheckEnabled').checked = s.model_check_enabled !== false;
                document.getElementById('modelCheckConfig').value = s.model_check_config || 'config/default.yaml';
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
            // Only update DOM content if autoscroll is on, or user is already
            // at the bottom — avoids yanking the viewport during copy/select.
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            const shouldScroll = document.getElementById('autoScrollScenario')?.checked;
            if (shouldScroll || atBottom) {
                el.textContent = text;
                if (shouldScroll) el.scrollTop = el.scrollHeight;
            } else {
                // Append only new lines so existing selection is not destroyed
                const newText = text.slice(_lastRenderedLength ?? 0);
                if (newText) el.textContent += newText;
            }
            _lastRenderedLength = text.length;
        } catch (e) { /* network */ }
    }

    async function updateStoredPositions() {
        try {
            const r = await fetch('/api/positions/get');
            const positions = await r.json();
            const el = document.getElementById('storedPositionsInfo');
            if (!el) return;

            if (!positions.start && !positions.goal) {
                el.innerHTML = '<div class="no-stored-positions">No positions stored</div>';
                return;
            }

            let html = '';
            if (positions.start) {
                const { lat, lng, psi, utm } = positions.start;
                html += `<div class="position-item">
                    <strong>🟢 Start</strong><br>
                    ${lat.toFixed(6)}, ${lng.toFixed(6)}&nbsp;|&nbsp;ψ=${(psi||0).toFixed(3)} rad<br>
                    <code>Position(lat_long=(${lat.toFixed(6)}, ${lng.toFixed(6)}), psi=${(psi||0).toFixed(3)})</code>
                </div>`;
            }
            if (positions.goal) {
                const { lat, lng, utm } = positions.goal;
                html += `<div class="position-item">
                    <strong>🔴 Goal</strong><br>
                    ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
                    <code>Position(lat_long=(${lat.toFixed(6)}, ${lng.toFixed(6)}))</code>
                </div>`;
            }
            el.innerHTML = html;
        } catch (e) { /* network */ }
    }

    async function applyPositions() {
        const r = await fetch('/api/positions/get');
        const positions = await r.json();
        if (!positions.start && !positions.goal) {
            alert('No stored positions. Use Goal Picker first.');
            return;
        }
        let lines = editorValue().split('\n');
        if (positions.start) {
            const line = `start_position = Position(lat_long=(${positions.start.lat.toFixed(6)}, ${positions.start.lng.toFixed(6)}), psi=${(positions.start.psi||0).toFixed(3)})`;
            const idx = lines.findIndex(l => l.trim().startsWith('start_position = Position('));
            if (idx >= 0) lines[idx] = line; else lines.unshift(line);
        }
        if (positions.goal) {
            const line = `goal_position = Position(lat_long=(${positions.goal.lat.toFixed(6)}, ${positions.goal.lng.toFixed(6)}))`;
            const idx = lines.findIndex(l => l.trim().startsWith('goal_position = Position('));
            if (idx >= 0) lines[idx] = line; else lines.push(line);
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

    function init() {
        initEditor();
        loadScenarios();
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
            if (confirm('Clear editor?')) setEditorValue(DEFAULT_LAUNCH);
        });
        document.getElementById('applyPositionsBtn')?.addEventListener('click', applyPositions);
        document.getElementById('clearPositionsBtn')?.addEventListener('click', clearPositions);

        const loopInputs = ['loopMode', 'loopDelay', 'loopRuntime', 'modelCheckEnabled', 'modelCheckConfig'];
        loopInputs.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.addEventListener('focus', () => { _isEditingLoop = true; });
            el.addEventListener('blur', () => { _isEditingLoop = false; });
            el.addEventListener('change', () => {
                clearTimeout(_loopDebounce);
                _loopDebounce = setTimeout(toggleLoopMode, 600);
            });
            el.addEventListener('input', () => {
                clearTimeout(_loopDebounce);
                _loopDebounce = setTimeout(toggleLoopMode, 1000);
            });
        });

        setInterval(updateStatus, 1000);
        setInterval(updateLog, 2000);
        setInterval(updateStoredPositions, 5000);
    }

    window.addEventListener('DOMContentLoaded', init);
    window.ScenarioMgr = { editorValue, setEditorValue };
})();
