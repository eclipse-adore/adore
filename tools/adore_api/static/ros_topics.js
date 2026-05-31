// ── ROS Topics Tab ────────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _selectedTopic = null;
    let _streamSource = null;
    let _autoScroll = true;
    let _pendingLines = [];
    let _rafPending = false;
    const MAX_LOG_LINES = 500;

    let _topicDatatypes = {};
    let _capturedMessages = [];

    let _publishLoopActive = false;
    let _importedMessages = [];
    let _importIdx = 0;

    function escHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function syntaxHighlightJson(obj) {
        const json = JSON.stringify(obj, null, 2);
        return json.replace(/(\"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*\"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, match => {
            if (/^"/.test(match)) {
                if (/:$/.test(match)) return `<span class="json-key">${escHtml(match)}</span>`;
                return `<span class="json-str">${escHtml(match)}</span>`;
            }
            if (/true|false/.test(match)) return `<span class="json-bool">${match}</span>`;
            if (/null/.test(match)) return `<span class="json-null">${match}</span>`;
            return `<span class="json-num">${match}</span>`;
        });
    }

    // ── Observe log ──────────────────────────────────────────────────────────

    function flushLogLines() {
        _rafPending = false;
        if (!_pendingLines.length) return;
        const log = document.getElementById('rosTopicObserveLog');
        if (!log) { _pendingLines = []; return; }

        const frag = document.createDocumentFragment();
        for (const { text, isErr } of _pendingLines) {
            const div = document.createElement('div');
            if (isErr) div.style.color = '#f85149';
            div.textContent = text;
            frag.appendChild(div);
        }
        _pendingLines = [];
        log.appendChild(frag);

        const excess = log.children.length - MAX_LOG_LINES;
        if (excess > 0) {
            const range = document.createRange();
            range.setStartBefore(log.firstChild);
            range.setEndBefore(log.children[excess]);
            range.deleteContents();
        }

        if (_autoScroll) log.scrollTop = log.scrollHeight;
    }

    function appendToObserveLog(text, isErr) {
        _pendingLines.push({ text, isErr });
        if (!_rafPending) {
            _rafPending = true;
            requestAnimationFrame(flushLogLines);
        }
    }

    // ── Publish log ──────────────────────────────────────────────────────────

    function appendToPublishLog(text, isErr) {
        const log = document.getElementById('rosPublishLog');
        if (!log) return;
        const div = document.createElement('div');
        div.style.color = isErr ? '#f85149' : '#3fb950';
        div.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        log.appendChild(div);
        const excess = log.children.length - MAX_LOG_LINES;
        if (excess > 0) {
            const r = document.createRange();
            r.setStartBefore(log.firstChild);
            r.setEndBefore(log.children[excess]);
            r.deleteContents();
        }
        log.scrollTop = log.scrollHeight;
    }

    // ── Topic list ───────────────────────────────────────────────────────────

    let _allTopics = [];
    let _allDatatypes = [];
    let _topicFilter = '';

    function fuzzyMatch(str, query) {
        if (!query) return true;
        str = str.toLowerCase(); query = query.toLowerCase();
        let qi = 0;
        for (let i = 0; i < str.length && qi < query.length; i++) {
            if (str[i] === query[qi]) qi++;
        }
        return qi === query.length;
    }

    function renderTopicList() {
        const listEl = document.getElementById('rosTopicList');
        if (!listEl) return;
        const filtered = _allTopics.filter(t => fuzzyMatch(t, _topicFilter));
        document.getElementById('rosTopicCount').textContent =
            _topicFilter ? `${filtered.length} / ${_allTopics.length}` : _allTopics.length;
        if (!filtered.length) {
            listEl.innerHTML = `<div class="no-running-nodes">${_allTopics.length ? 'No matches' : 'No topics found — is ROS running?'}</div>`;
            return;
        }
        listEl.innerHTML = filtered.map(t => {
            const dt = _topicDatatypes[t] ? `<span class="topic-datatype">${escHtml(_topicDatatypes[t])}</span>` : '';
            return `<div class="topic-list-item${_selectedTopic === t ? ' topic-selected' : ''}" data-topic="${escHtml(t)}">${escHtml(t)}${dt}</div>`;
        }).join('');
        listEl.querySelectorAll('.topic-list-item').forEach(el => {
            el.addEventListener('click', () => selectTopic(el.dataset.topic, el));
        });
    }

    async function loadTopicList() {
        const listEl = document.getElementById('rosTopicList');
        if (!listEl) return;
        listEl.innerHTML = '<div class="no-running-nodes">Loading...</div>';
        try {
            const r = await fetch('/api/topic/list');
            const d = await r.json();
            _allTopics = (d.system_topics || []).sort();
            _topicDatatypes = d.topic_datatypes || {};
            _allDatatypes = [...new Set(Object.values(_topicDatatypes).filter(Boolean))].sort();
            renderTopicList();
        } catch (e) {
            listEl.innerHTML = `<div class="no-running-nodes" style="color:#f85149;">Error: ${escHtml(String(e))}</div>`;
        }
        // Load full type list in background — does not block the topic list render
        loadInterfaceTypes();
    }

    async function loadInterfaceTypes() {
        try {
            const r = await fetch('/api/topic/interface_types');
            const d = await r.json();
            if (d.types && d.types.length) {
                const merged = new Set([..._allDatatypes, ...d.types]);
                _allDatatypes = [...merged].sort();
            }
        } catch {}
    }

    function selectTopic(topic, el) {
        _selectedTopic = topic;
        document.querySelectorAll('#rosTopicList .topic-list-item').forEach(i => i.classList.remove('topic-selected'));
        if (el) el.classList.add('topic-selected');

        const selEl = document.getElementById('rosTopicSelected');
        if (selEl) selEl.value = topic;

        setVal('rosTopicObserveInput', topic);
        setVal('rosTopicHzInput', topic);
        setVal('rosTopicEchoInput', topic);
        setVal('rosPublishTopicInput', topic);

        const dt = _topicDatatypes[topic] || '';
        if (dt) setVal('rosPublishDatatypeInput', dt);
    }

    function setVal(id, val) {
        const el = document.getElementById(id);
        if (el) el.value = val;
    }

    // ── Fuzzy dropdown ───────────────────────────────────────────────────────

    function createTopicDropdown(inputId, dropdownId, getItems, onSelect) {
        const input = document.getElementById(inputId);
        const dropdown = document.getElementById(dropdownId);
        if (!input || !dropdown) return;

        function showDropdown() {
            const query = input.value.trim();
            const items = getItems().filter(t => fuzzyMatch(t, query));
            if (!items.length) { dropdown.style.display = 'none'; return; }
            dropdown.innerHTML = items.slice(0, 50).map(t => {
                const dt = _topicDatatypes[t];
                const dtSpan = dt ? `<span class="topic-dropdown-dt">${escHtml(dt)}</span>` : '';
                return `<div class="topic-dropdown-item" data-value="${escHtml(t)}">${escHtml(t)}${dtSpan}</div>`;
            }).join('');
            dropdown.querySelectorAll('.topic-dropdown-item').forEach(el => {
                el.addEventListener('mousedown', e => {
                    e.preventDefault();
                    input.value = el.dataset.value;
                    dropdown.style.display = 'none';
                    if (onSelect) onSelect(el.dataset.value);
                });
            });
            dropdown.style.display = 'block';
        }

        input.addEventListener('input', showDropdown);
        input.addEventListener('focus', showDropdown);
        input.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 150));
        input.addEventListener('keydown', e => {
            if (e.key === 'Escape') { dropdown.style.display = 'none'; input.blur(); }
            if (e.key === 'Enter') dropdown.style.display = 'none';
        });
    }

    function setupDatatypeDropdown() {
        const input = document.getElementById('rosPublishDatatypeInput');
        const dropdown = document.getElementById('rosPublishDatatypeDropdown');
        if (!input || !dropdown) return;

        function show() {
            const query = input.value.trim();
            const items = _allDatatypes.filter(dt => fuzzyMatch(dt, query));
            if (!items.length) { dropdown.style.display = 'none'; return; }
            dropdown.innerHTML = items.slice(0, 50).map(dt =>
                `<div class="topic-dropdown-item" data-value="${escHtml(dt)}">${escHtml(dt)}</div>`
            ).join('');
            dropdown.querySelectorAll('.topic-dropdown-item').forEach(el => {
                el.addEventListener('mousedown', e => {
                    e.preventDefault();
                    input.value = el.dataset.value;
                    dropdown.style.display = 'none';
                });
            });
            dropdown.style.display = 'block';
        }

        input.addEventListener('input', show);
        input.addEventListener('focus', show);
        input.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 150));
        input.addEventListener('keydown', e => {
            if (e.key === 'Escape') { dropdown.style.display = 'none'; input.blur(); }
        });
    }

    // ── Stream ───────────────────────────────────────────────────────────────

    function getMaxHz() {
        const el = document.getElementById('rosObserveMaxHz');
        const v = el ? parseFloat(el.value) : 10;
        return isFinite(v) && v > 0 ? Math.min(v, 20) : 10;
    }

    function startStream(topic) {
        if (_streamSource) { _streamSource.close(); _streamSource = null; }
        _pendingLines = [];
        _capturedMessages = [];
        const log = document.getElementById('rosTopicObserveLog');
        if (log) log.innerHTML = '';
        appendToObserveLog(`[streaming] ${topic} @ max ${getMaxHz()} Hz`, false);

        const url = `/api/topic/stream?topic=${encodeURIComponent(topic)}&max_hz=${getMaxHz()}`;
        _streamSource = new EventSource(url);
        _streamSource.onmessage = e => {
            try {
                const d = JSON.parse(e.data);
                if (d.error) { appendToObserveLog('[error] ' + d.error, true); return; }
                const dropped = d.dropped ? ` \u2946${d.dropped}` : '';
                const header = `[${d.time}]${dropped}`;
                const body = d.msg !== undefined ? JSON.stringify(d.msg, null, 2) : (d.text || '');
                appendToObserveLog(header + '\n' + body, false);
                if (d.msg !== undefined) _capturedMessages.push(d.msg);
            } catch { appendToObserveLog(e.data, false); }
        };
        _streamSource.onerror = () => appendToObserveLog('[stream disconnected]', true);
        document.getElementById('rosObserveStopBtn').disabled = false;
        document.getElementById('rosObserveStartBtn').disabled = true;
    }

    function stopStream() {
        if (_streamSource) { _streamSource.close(); _streamSource = null; }
        appendToObserveLog('[stream stopped]', true);
        document.getElementById('rosObserveStopBtn').disabled = true;
        document.getElementById('rosObserveStartBtn').disabled = false;
    }

    function exportJsonl() {
        const countEl = document.getElementById('rosExportCount');
        const count = countEl ? Math.max(1, parseInt(countEl.value) || 10) : 10;
        const msgs = _capturedMessages.slice(-count);
        if (!msgs.length) { alert('No messages captured yet — start streaming first.'); return; }
        const topic = (document.getElementById('rosTopicObserveInput').value.trim() || 'topic').replace(/\//g, '_');
        const blob = new Blob([msgs.map(m => JSON.stringify(m)).join('\n')], { type: 'application/x-ndjson' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `${topic}_${Date.now()}.jsonl`; a.click();
        URL.revokeObjectURL(url);
    }

    // ── Hz ───────────────────────────────────────────────────────────────────

    async function runHz() {
        const topic = document.getElementById('rosTopicHzInput').value.trim();
        if (!topic) return;
        const out = document.getElementById('rosTopicHzOutput');
        if (out) out.textContent = 'Running ros2 topic hz -w 10 ...';
        try {
            const r = await fetch('/api/topic/hz', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic }),
            });
            const d = await r.json();
            if (out) out.textContent = d.success ? (d.output || '(no output)') : ('Error: ' + d.message);
        } catch (e) {
            if (out) out.textContent = 'Request failed: ' + e;
        }
    }

    // ── Echo ─────────────────────────────────────────────────────────────────

    async function echoOnce() {
        const topic = document.getElementById('rosTopicEchoInput').value.trim();
        if (!topic) return;
        const viewer = document.getElementById('rosTopicJsonViewer');
        if (viewer) viewer.innerHTML = '<span style="color:#6e7681">Waiting for message...</span>';
        try {
            const r = await fetch('/api/topic/echo', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic }),
            });
            const d = await r.json();
            if (!d.success) {
                if (viewer) viewer.innerHTML = `<span style="color:#f85149">Error: ${escHtml(d.message)}</span>`;
                return;
            }
            if (viewer) {
                if (d.msg !== undefined) {
                    viewer.innerHTML = syntaxHighlightJson(d.msg);
                } else if (d.raw) {
                    let parsed = null;
                    try { parsed = JSON.parse(d.raw); } catch {}
                    viewer.innerHTML = parsed !== null ? syntaxHighlightJson(parsed) : escHtml(d.raw);
                }
            }
        } catch (e) {
            if (viewer) viewer.innerHTML = `<span style="color:#f85149">Request failed: ${escHtml(String(e))}</span>`;
        }
    }

    // ── Publish editor (CodeMirror) ──────────────────────────────────────────

    let _publishEditor = null;

    function initPublishEditor() {
        const container = document.getElementById('rosPublishEditorContainer');
        if (!container || _publishEditor) return;
        try {
            _publishEditor = CodeMirror(container, {
                mode: { name: 'javascript', json: true },
                theme: 'monokai',
                lineNumbers: true,
                matchBrackets: true,
                autoCloseBrackets: true,
                indentUnit: 2,
                tabSize: 2,
                lineWrapping: false,
                value: '{}'
            });
            // Resize the CodeMirror wrapper to fill container
            _publishEditor.setSize('100%', '100%');
            _publishEditor.on('change', () => {
                try {
                    JSON.parse(_publishEditor.getValue());
                    setEditorError('');
                } catch (e) {
                    setEditorError(e.message);
                }
            });
            setTimeout(() => _publishEditor && _publishEditor.refresh(), 200);
        } catch (e) {
            console.warn('CodeMirror init failed for publish editor:', e);
        }
    }

    function getEditorValue() {
        return _publishEditor ? _publishEditor.getValue() : (document.getElementById('rosPublishEditorContainer')?.textContent || '{}');
    }

    function setEditorValue(val) {
        if (_publishEditor) {
            _publishEditor.setValue(val);
            _publishEditor.refresh();
        }
    }

    function setEditorError(msg) {
        const el = document.getElementById('rosPublishEditorError');
        if (el) el.textContent = msg || '';
    }

    function parseEditor() {
        try {
            const val = JSON.parse(getEditorValue());
            setEditorError('');
            return val;
        } catch (e) {
            setEditorError('JSON parse error: ' + e.message);
            return null;
        }
    }

    async function loadProtoTemplate() {
        const datatype = document.getElementById('rosPublishDatatypeInput').value.trim();
        if (!datatype) { setEditorError('Enter a datatype first'); return; }
        try {
            const r = await fetch('/api/topic/empty_message', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ datatype }),
            });
            const d = await r.json();
            if (!d.success) { setEditorError(d.message); return; }
            const msg = d.msg;
            if (msg === null || msg === undefined || typeof msg !== 'object' || Array.isArray(msg)) {
                setEditorError('Backend returned unexpected format — check ros2tools installation');
                appendToPublishLog(`Template load failed for ${datatype}: unexpected response type`, true);
                return;
            }
            setEditorValue(JSON.stringify(msg, null, 2));
            setEditorError('');
            appendToPublishLog(`Loaded template for ${datatype}`, false);
        } catch (e) {
            setEditorError('Request failed: ' + e);
        }
    }

    const _META_KEYS = new Set(['topic', 'datatype', 'WARNING', 'WARN', 'ERROR', 'INFO', 'DEBUG']);

    function stripMessageMeta(msg) {
        if (!msg || typeof msg !== 'object' || Array.isArray(msg)) return msg;
        const out = {};
        for (const [k, v] of Object.entries(msg)) {
            if (!_META_KEYS.has(k)) out[k] = v;
        }
        return out;
    }

    async function doPublish(data, topic, datatype, frequency) {
        const r = await fetch('/api/topic/publish_timed', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, datatype: datatype || undefined, data: stripMessageMeta(data), frequency: frequency || 0 }),
        });
        return r.json();
    }

    async function publishOnce() {
        const topic = document.getElementById('rosPublishTopicInput').value.trim();
        const datatype = document.getElementById('rosPublishDatatypeInput').value.trim();
        const data = parseEditor();
        if (!topic) { setEditorError('Topic required'); return; }
        if (data === null) return;
        try {
            const d = await doPublish(data, topic, datatype, 0);
            appendToPublishLog(d.success ? `Published to ${d.topic} [${d.datatype}]` : `Error: ${d.message}`, !d.success);
        } catch (e) { appendToPublishLog('Request failed: ' + e, true); }
    }

    async function startPublishLoop() {
        const topic = document.getElementById('rosPublishTopicInput').value.trim();
        const datatype = document.getElementById('rosPublishDatatypeInput').value.trim();
        const freq = parseFloat(document.getElementById('rosPublishFreqInput').value) || 1;
        const data = parseEditor();
        if (!topic) { setEditorError('Topic required'); return; }
        if (data === null) return;
        try {
            const d = await doPublish(data, topic, datatype, freq);
            if (d.success) {
                setPublishLoopUI(true);
                startStatusPoll(topic);
                appendToPublishLog(`Started persistent publisher on ${d.topic} at ${freq} Hz [${d.datatype}]`, false);
            } else {
                appendToPublishLog(`Error: ${d.message}`, true);
            }
        } catch (e) { appendToPublishLog('Request failed: ' + e, true); }
    }

    async function stopPublishLoop() {
        const topic = document.getElementById('rosPublishTopicInput').value.trim();
        if (!topic) return;
        try {
            await fetch('/api/topic/publish_timed', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, action: 'stop', data: {} }),
            });
        } catch {}
        setPublishLoopUI(false);
        stopStatusPoll();
        appendToPublishLog(`Stopped loop on ${topic}`, false);
    }

    function handleImportFile(file) {
        const reader = new FileReader();
        reader.onload = e => {
            const lines = e.target.result.split('\n').filter(l => l.trim());
            _importedMessages = [];
            for (const line of lines) {
                try { _importedMessages.push(JSON.parse(line)); } catch {}
            }
            _importIdx = 0;
            updateImportUI();
            if (_importedMessages.length) {
                setEditorValue(JSON.stringify(_importedMessages[0], null, 2));
                appendToPublishLog(`Imported ${_importedMessages.length} messages from ${file.name}`, false);
            }
        };
        reader.readAsText(file);
    }

    function updateImportUI() {
        const container = document.getElementById('rosPublishImportList');
        if (!container) return;
        if (_importedMessages.length) {
            container.style.display = 'block';
            const cEl = document.getElementById('rosPublishImportCount');
            const iEl = document.getElementById('rosPublishImportIdx');
            if (cEl) cEl.textContent = _importedMessages.length;
            if (iEl) iEl.textContent = _importIdx + 1;
        } else {
            container.style.display = 'none';
        }
    }

    function navImport(dir) {
        if (!_importedMessages.length) return;
        _importIdx = (_importIdx + dir + _importedMessages.length) % _importedMessages.length;
        updateImportUI();
        setEditorValue(JSON.stringify(_importedMessages[_importIdx], null, 2));
    }

    let _statusPollTimer = null;

    function startStatusPoll(topic) {
        stopStatusPoll();
        _statusPollTimer = setInterval(async () => {
            try {
                const r = await fetch('/api/topic/publish_status');
                const d = await r.json();
                if (!d.active || !d.active[topic]) {
                    appendToPublishLog(`[status] Session on ${topic} ended`, false);
                    setPublishLoopUI(false);
                    stopStatusPoll();
                }
            } catch {}
        }, 2000);
    }

    function stopStatusPoll() {
        if (_statusPollTimer) { clearInterval(_statusPollTimer); _statusPollTimer = null; }
    }

    function setPublishLoopUI(active) {
        _publishLoopActive = active;
        document.getElementById('rosPublishStartBtn').disabled = active;
        document.getElementById('rosPublishStopBtn').disabled = !active;
        const replayBtn = document.getElementById('rosPublishImportReplayBtn');
        const replayStop = document.getElementById('rosPublishImportStopBtn');
        if (replayBtn) replayBtn.disabled = active;
        if (replayStop) replayStop.disabled = !active;
    }

    async function replayImported() {
        if (!_importedMessages.length) return;
        const topic = document.getElementById('rosPublishTopicInput').value.trim();
        const datatype = document.getElementById('rosPublishDatatypeInput').value.trim();
        const freq = parseFloat(document.getElementById('rosPublishFreqInput').value) || 1;
        const loop = document.getElementById('rosPublishLoopReplay')?.checked || false;
        if (!topic) { setEditorError('Topic required'); return; }

        const messages = _importedMessages.map(stripMessageMeta);
        try {
            const r = await fetch('/api/topic/publish_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, datatype: datatype || undefined, messages, frequency: freq, loop }),
            });
            const d = await r.json();
            if (d.success) {
                appendToPublishLog(`Batch started: ${d.messages} messages @ ${d.frequency} Hz${loop ? ' (looping)' : ''}`, false);
                setPublishLoopUI(true);
                startStatusPoll(topic);
            } else {
                appendToPublishLog(`Error: ${d.message}`, true);
            }
        } catch (e) {
            appendToPublishLog('Request failed: ' + e, true);
        }
    }

    async function stopReplay() {
        const topic = document.getElementById('rosPublishTopicInput').value.trim();
        if (!topic) return;
        await fetch('/api/topic/publish_timed', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, action: 'stop', data: {} }),
        });
        setPublishLoopUI(false);
        stopStatusPoll();
        appendToPublishLog(`Stopped batch on ${topic}`, false);
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    function init() {
        document.getElementById('rosTopicRefreshBtn')?.addEventListener('click', loadTopicList);
        document.getElementById('rosObserveStartBtn')?.addEventListener('click', () => {
            const t = document.getElementById('rosTopicObserveInput').value.trim();
            if (t) startStream(t);
        });
        document.getElementById('rosObserveStopBtn')?.addEventListener('click', stopStream);
        document.getElementById('rosTopicHzBtn')?.addEventListener('click', runHz);
        document.getElementById('rosTopicEchoBtn')?.addEventListener('click', echoOnce);
        document.getElementById('rosObserveAutoScroll')?.addEventListener('change', e => { _autoScroll = e.target.checked; });
        document.getElementById('rosExportJsonlBtn')?.addEventListener('click', exportJsonl);

        document.getElementById('rosObserveMaxHz')?.addEventListener('change', () => {
            if (_streamSource) {
                const topic = document.getElementById('rosTopicObserveInput').value.trim();
                if (topic) startStream(topic);
            }
        });

        document.getElementById('rosTopicSearch')?.addEventListener('input', e => {
            _topicFilter = e.target.value;
            renderTopicList();
        });

        // Publish
        document.getElementById('rosPublishLoadProtoBtn')?.addEventListener('click', loadProtoTemplate);
        document.getElementById('rosPublishOnceBtn')?.addEventListener('click', publishOnce);
        document.getElementById('rosPublishStartBtn')?.addEventListener('click', startPublishLoop);
        document.getElementById('rosPublishStopBtn')?.addEventListener('click', stopPublishLoop);
        document.getElementById('rosPublishClearLogBtn')?.addEventListener('click', () => {
            const log = document.getElementById('rosPublishLog');
            if (log) log.innerHTML = '';
        });
        document.getElementById('rosPublishImportFile')?.addEventListener('change', e => {
            if (e.target.files[0]) handleImportFile(e.target.files[0]);
            e.target.value = '';
        });
        document.getElementById('rosPublishImportPrevBtn')?.addEventListener('click', () => navImport(-1));
        document.getElementById('rosPublishImportNextBtn')?.addEventListener('click', () => navImport(1));
        document.getElementById('rosPublishImportClearBtn')?.addEventListener('click', () => {
            _importedMessages = []; _importIdx = 0; updateImportUI();
        });
        document.getElementById('rosPublishImportReplayBtn')?.addEventListener('click', replayImported);
        document.getElementById('rosPublishImportStopBtn')?.addEventListener('click', stopReplay);

        document.getElementById('rosPublishTopicInput')?.addEventListener('change', e => {
            const dt = _topicDatatypes[e.target.value.trim()];
            if (dt) setVal('rosPublishDatatypeInput', dt);
        });

        // Fuzzy dropdowns
        createTopicDropdown('rosTopicObserveInput', 'rosObserveDropdown', () => _allTopics, null);
        createTopicDropdown('rosTopicHzInput', 'rosHzDropdown', () => _allTopics, null);
        createTopicDropdown('rosTopicEchoInput', 'rosEchoDropdown', () => _allTopics, null);
        createTopicDropdown('rosPublishTopicInput', 'rosPublishTopicDropdown', () => _allTopics, topic => {
            const dt = _topicDatatypes[topic];
            if (dt) setVal('rosPublishDatatypeInput', dt);
        });
        setupDatatypeDropdown();

        // Init CodeMirror editor when Publish tab is clicked (deferred so container is visible)
        document.querySelector('[data-logtab="ros-topics-publish"]')?.addEventListener('click', () => {
            setTimeout(initPublishEditor, 50);
        });

        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'ros-topics') loadTopicList();
        });
    }

    window.addEventListener('DOMContentLoaded', init);
})();
