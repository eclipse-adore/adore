// ── ROS Topics Tab ────────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _selectedTopic = null;
    let _streamSource = null;
    let _autoScroll = true;
    let _pendingLines = [];     // lines waiting for next rAF flush
    let _rafPending = false;
    const MAX_LOG_LINES = 500;

    function escHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function syntaxHighlightJson(obj) {
        const json = JSON.stringify(obj, null, 2);
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, match => {
            if (/^"/.test(match)) {
                if (/:$/.test(match)) return `<span class="json-key">${escHtml(match)}</span>`;
                return `<span class="json-str">${escHtml(match)}</span>`;
            }
            if (/true|false/.test(match)) return `<span class="json-bool">${match}</span>`;
            if (/null/.test(match)) return `<span class="json-null">${match}</span>`;
            return `<span class="json-num">${match}</span>`;
        });
    }

    // Batch all pending log lines in one rAF, then trim the buffer in one splice
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

        // Trim to MAX_LOG_LINES in one operation
        const excess = log.children.length - MAX_LOG_LINES;
        if (excess > 0) {
            const range = document.createRange();
            range.setStartBefore(log.firstChild);
            range.setEndBefore(log.children[excess]);
            range.deleteContents();
        }

        if (_autoScroll) {
            log.scrollTop = log.scrollHeight;
        }
    }

    function appendToObserveLog(text, isErr) {
        _pendingLines.push({ text, isErr });
        if (!_rafPending) {
            _rafPending = true;
            requestAnimationFrame(flushLogLines);
        }
    }

    let _allTopics = [];
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
        listEl.innerHTML = filtered.map(t => `
            <div class="topic-list-item${_selectedTopic === t ? ' topic-selected' : ''}" data-topic="${escHtml(t)}">${escHtml(t)}</div>
        `).join('');
        listEl.querySelectorAll('.topic-list-item').forEach(el => {
            el.addEventListener('click', () => selectTopic(el.dataset.topic, el));
        });
    }

    async function loadTopicList() {
        const listEl = document.getElementById('rosTopicList');
        if (!listEl) return;
        listEl.innerHTML = '<div class="no-running-nodes">Loading…</div>';
        try {
            const r = await fetch('/api/topic/list');
            const d = await r.json();
            _allTopics = (d.system_topics || []).sort();
            renderTopicList();
        } catch (e) {
            listEl.innerHTML = `<div class="no-running-nodes" style="color:#f85149;">Error: ${escHtml(String(e))}</div>`;
        }
    }

    function selectTopic(topic, el) {
        _selectedTopic = topic;
        document.querySelectorAll('#rosTopicList .topic-list-item').forEach(i => i.classList.remove('topic-selected'));
        if (el) el.classList.add('topic-selected');
        document.getElementById('rosTopicSelected').value = topic;
        document.getElementById('rosTopicObserveInput').value = topic;
        document.getElementById('rosTopicHzInput').value = topic;
        document.getElementById('rosTopicEchoInput').value = topic;
    }

    function getMaxHz() {
        const el = document.getElementById('rosObserveMaxHz');
        const v = el ? parseFloat(el.value) : 10;
        return isFinite(v) && v > 0 ? Math.min(v, 20) : 10;
    }

    function startStream(topic) {
        if (_streamSource) { _streamSource.close(); _streamSource = null; }
        _pendingLines = [];
        const log = document.getElementById('rosTopicObserveLog');
        if (log) log.innerHTML = '';
        appendToObserveLog(`[streaming] ${topic} @ max ${getMaxHz()} Hz`, false);

        const url = `/api/topic/stream?topic=${encodeURIComponent(topic)}&max_hz=${getMaxHz()}`;
        _streamSource = new EventSource(url);
        _streamSource.onmessage = e => {
            try {
                const d = JSON.parse(e.data);
                if (d.error) { appendToObserveLog('[error] ' + d.error, true); return; }
                const dropped = d.dropped ? ` ⤵${d.dropped}` : '';
                const header = `[${d.time}]${dropped}`;
                // msg is a parsed object from ROSMarshaller — render as compact JSON
                const body = d.msg !== undefined
                    ? JSON.stringify(d.msg, null, 2)
                    : (d.text || '');
                appendToObserveLog(header + '\n' + body, false);
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

    async function runHz() {
        const topic = document.getElementById('rosTopicHzInput').value.trim();
        if (!topic) return;
        const out = document.getElementById('rosTopicHzOutput');
        if (out) out.textContent = 'Running ros2 topic hz -w 10 …';
        try {
            const r = await fetch('/api/topic/hz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic }),
            });
            const d = await r.json();
            if (out) out.textContent = d.success ? (d.output || '(no output)') : ('Error: ' + d.message);
        } catch (e) {
            if (out) out.textContent = 'Request failed: ' + e;
        }
    }

    async function echoOnce() {
        const topic = document.getElementById('rosTopicEchoInput').value.trim();
        if (!topic) return;
        const viewer = document.getElementById('rosTopicJsonViewer');
        if (viewer) viewer.innerHTML = '<span style="color:#6e7681">Waiting for message…</span>';
        try {
            const r = await fetch('/api/topic/echo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic }),
            });
            const d = await r.json();
            if (!d.success) {
                if (viewer) viewer.innerHTML = `<span style="color:#f85149">Error: ${escHtml(d.message)}</span>`;
                return;
            }
            let parsed = null;
            try { parsed = JSON.parse(d.raw); } catch { /* yaml/plain text */ }
            if (viewer) {
                viewer.innerHTML = parsed !== null
                    ? syntaxHighlightJson(parsed)
                    : escHtml(d.raw);
            }
        } catch (e) {
            if (viewer) viewer.innerHTML = `<span style="color:#f85149">Request failed: ${escHtml(String(e))}</span>`;
        }
    }

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

        // Restart stream when Hz setting changes while a stream is active
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

        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'ros-topics') loadTopicList();
        });
    }

    window.addEventListener('DOMContentLoaded', init);
})();
