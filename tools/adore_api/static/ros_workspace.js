// ── ROS Workspace Tab ─────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _logSource = null;
    let _autoScroll = true;
    let _packages = [];
    let _pkgFilter = '';
    let _autoRebuildEnabled = false;          // global toggle
    let _autoRebuildPkgs = new Set();         // per-package opt-in
    let _autoRebuildTimer = null;
    let _rebuilding = new Set();              // currently building via auto-rebuild

    const AUTO_REBUILD_INTERVAL_MS = 5000;

    function escHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function appendLog(text, isErr) {
        const log = document.getElementById('wsLogContainer');
        if (!log) return;
        const line = document.createElement('div');
        if (isErr) line.style.color = '#f85149';
        line.textContent = text;
        log.appendChild(line);
        if (_autoScroll) log.scrollTop = log.scrollHeight;
        while (log.children.length > 5000) log.removeChild(log.firstChild);
    }

    function connectLogStream() {
        if (_logSource) return;
        _logSource = new EventSource('/api/ros_workspace/log/stream');
        _logSource.onmessage = e => {
            try {
                const d = JSON.parse(e.data);
                appendLog(d.text, d.stream === 'stderr');
            } catch { appendLog(e.data, false); }
        };
    }

    async function loadStatus() {
        const grid = document.getElementById('wsStatusGrid');
        if (!grid) return;
        try {
            const r = await fetch('/api/ros_workspace/status');
            const d = await r.json();
            const builtPkgs = d.built_packages ?? '?';
            const totalPkgs = d.total_packages ?? '?';
            const pkgOk = typeof d.built_packages === 'number' && d.built_packages === d.total_packages;
            grid.innerHTML = `
                <span class="ws-key">Workspace dir</span><span class="ws-val">${escHtml(d.workspace_dir)}</span>
                <span class="ws-key">Workspace exists</span><span class="ws-val ${d.workspace_exists ? 'ok' : 'err'}">${d.workspace_exists ? '✓' : '✗'}</span>
                <span class="ws-key">Makefile</span><span class="ws-val ${d.makefile_exists ? 'ok' : 'err'}">${d.makefile_exists ? '✓ found' : '✗ not found'}</span>
                <span class="ws-key">build/</span><span class="ws-val ${d.build_dir_exists ? 'ok' : 'err'}">${d.build_dir_exists ? '✓ exists' : '✗ missing'}</span>
                <span class="ws-key">install/</span><span class="ws-val ${d.install_dir_exists ? 'ok' : 'err'}">${d.install_dir_exists ? '✓ exists' : '✗ missing'}</span>
                <span class="ws-key">Packages built</span><span class="ws-val ${pkgOk ? 'ok' : 'err'}">${builtPkgs} / ${totalPkgs}</span>
                <span class="ws-key">make clean</span><span class="ws-val ${d.running?.clean ? 'ok' : ''}">${d.running?.clean ? '⟳ running' : 'idle'}</span>
                <span class="ws-key">make build</span><span class="ws-val ${d.running?.build ? 'ok' : ''}">${d.running?.build ? '⟳ running' : 'idle'}</span>
            `;
            const cleanBtn = document.getElementById('wsCleanBtn');
            const buildBtn = document.getElementById('wsBuildBtn');
            if (cleanBtn) cleanBtn.disabled = !!(d.running?.clean || d.running?.build);
            if (buildBtn) buildBtn.disabled = !!(d.running?.clean || d.running?.build);
        } catch (e) {
            grid.innerHTML = `<span class="ws-val err" style="grid-column:1/-1">Failed to load status: ${escHtml(String(e))}</span>`;
        }
    }

    async function loadPackages() {
        const el = document.getElementById('wsPackageList');
        if (!el) return;
        try {
            const r = await fetch('/api/ros_workspace/packages');
            const d = await r.json();
            _packages = d.packages || [];
            // Remove auto-rebuild for newly discovered unknown packages
            _packages.filter(p => p.colcon_unknown).forEach(p => _autoRebuildPkgs.delete(p.name));
            renderPackages();
        } catch (e) {
            el.innerHTML = `<div class="no-running-nodes" style="color:#f85149;">Error: ${escHtml(String(e))}</div>`;
        }
    }

    function fuzzyMatch(str, query) {
        if (!query) return true;
        str = str.toLowerCase(); query = query.toLowerCase();
        let qi = 0;
        for (let i = 0; i < str.length && qi < query.length; i++) {
            if (str[i] === query[qi]) qi++;
        }
        return qi === query.length;
    }

    function renderPackages() {
        const el = document.getElementById('wsPackageList');
        if (!el) return;
        const q = _pkgFilter.toLowerCase();
        const filtered = _packages.filter(p => fuzzyMatch(p.name, q));
        const total = document.getElementById('wsPkgCount');
        if (total) total.textContent = _pkgFilter ? `${filtered.length} / ${_packages.length}` : _packages.length;
        if (!filtered.length) {
            el.innerHTML = `<div class="no-running-nodes">${_packages.length ? 'No matches' : 'No packages found in src/'}</div>`;
            return;
        }
        el.innerHTML = filtered.map(p => {
            const indClass = !p.built ? 'pkg-not-built' : p.stale ? 'pkg-stale' : 'pkg-built';
            const indTitle = !p.built ? 'Not built' : p.stale ? 'Built but source has changed' : 'Built and up to date';
            const unknown = p.colcon_unknown;
            const autoChecked = _autoRebuildPkgs.has(p.name) && !unknown ? 'checked' : '';
            const autoDisabled = unknown ? 'disabled title="colcon cannot find this package"' : '';
            const rebuildingClass = _rebuilding.has(p.name) ? ' pkg-rebuilding' : '';
            return `<div class="pkg-list-item${rebuildingClass}" data-pkg="${escHtml(p.name)}">
                <span class="pkg-indicator ${indClass}" title="${indTitle}"></span>
                <span class="pkg-name${unknown ? ' pkg-unknown' : ''}" title="${unknown ? 'Not known to colcon — excluded from auto-rebuild' : ''}">${escHtml(p.name)}</span>
                <label class="pkg-auto-label" title="Auto-rebuild on change">
                    <input type="checkbox" class="pkg-auto-cb" data-pkg="${escHtml(p.name)}" ${autoChecked} ${autoDisabled}>
                    Auto
                </label>
                <button class="btn-info pkg-build-btn" data-pkg="${escHtml(p.name)}"${unknown ? ' title="colcon cannot find this package"' : ` title="colcon build --packages-select ${escHtml(p.name)}"`}${unknown ? ' disabled' : ''}>Build</button>
            </div>`;
        }).join('');
        el.querySelectorAll('.pkg-build-btn').forEach(btn => {
            btn.addEventListener('click', () => buildPackage(btn.dataset.pkg));
        });
        el.querySelectorAll('.pkg-auto-cb').forEach(cb => {
            cb.addEventListener('change', e => {
                const pkg = e.target.dataset.pkg;
                if (e.target.checked) _autoRebuildPkgs.add(pkg);
                else _autoRebuildPkgs.delete(pkg);
            });
        });
    }

    async function buildPackage(pkg, isAuto = false) {
        if (_rebuilding.has(pkg)) return;
        _rebuilding.add(pkg);
        if (isAuto) appendLog(`[auto-rebuild] ${pkg}`, false);
        try {
            const r = await fetch('/api/ros_workspace/build_package', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ package: pkg }),
            });
            const d = await r.json();
            if (!d.success) {
                appendLog(`Error: ${d.message}`, true);
                _rebuilding.delete(pkg);
                return;
            }
            const key = `__pkg__${pkg}`;
            const poll = setInterval(async () => {
                try {
                    const sr = await fetch('/api/ros_workspace/status').then(r => r.json());
                    if (!sr.running?.[key]) {
                        clearInterval(poll);
                        _rebuilding.delete(pkg);
                        loadPackages();
                        renderPackages();
                    }
                } catch { clearInterval(poll); _rebuilding.delete(pkg); }
            }, 2000);
        } catch (e) {
            appendLog(`Request failed: ${e}`, true);
            _rebuilding.delete(pkg);
        }
        renderPackages();
    }

    function runAutoRebuildCheck() {
        if (!_autoRebuildEnabled) return;
        _packages.forEach(p => {
            if (p.stale && !p.colcon_unknown && _autoRebuildPkgs.has(p.name) && !_rebuilding.has(p.name)) {
                buildPackage(p.name, true);
            }
        });
    }

    function setAutoRebuild(enabled) {
        _autoRebuildEnabled = enabled;
        if (enabled) {
            // Refresh package list immediately then start polling
            loadPackages();
            _autoRebuildTimer = setInterval(async () => {
                await loadPackages();
                runAutoRebuildCheck();
            }, AUTO_REBUILD_INTERVAL_MS);
        } else {
            if (_autoRebuildTimer) { clearInterval(_autoRebuildTimer); _autoRebuildTimer = null; }
        }
    }

    async function runMake(target) {
        const r = await fetch(`/api/ros_workspace/${target}`, { method: 'POST' });
        const d = await r.json();
        appendLog(d.success ? `[${target}] started` : `[${target}] error: ${d.message}`, !d.success);
        setTimeout(loadStatus, 500);
        const poll = setInterval(() => {
            loadStatus();
            fetch('/api/ros_workspace/status').then(r => r.json()).then(d => {
                if (!d.running?.[target]) { clearInterval(poll); loadPackages(); }
            }).catch(() => clearInterval(poll));
        }, 2000);
    }

    function init() {
        document.getElementById('wsRefreshBtn')?.addEventListener('click', () => { loadStatus(); loadPackages(); });
        document.getElementById('wsCleanBtn')?.addEventListener('click', () => runMake('clean'));
        document.getElementById('wsBuildBtn')?.addEventListener('click', () => runMake('build'));
        document.getElementById('wsClearLogBtn')?.addEventListener('click', () => {
            const log = document.getElementById('wsLogContainer');
            if (log) log.innerHTML = '';
        });
        document.getElementById('wsAutoScroll')?.addEventListener('change', e => { _autoScroll = e.target.checked; });
        document.getElementById('wsPkgSearch')?.addEventListener('input', e => { _pkgFilter = e.target.value; renderPackages(); });
        document.getElementById('wsAutoRebuildToggle')?.addEventListener('change', e => setAutoRebuild(e.target.checked));

        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'ros-workspace') { loadStatus(); loadPackages(); connectLogStream(); }
        });
    }

    window.addEventListener('DOMContentLoaded', init);
})();
