// ── Model Checker Results Side Panel ─────────────────────────────────────────
(function () {
    'use strict';

    let _runId = null;
    let _status = 'idle';
    let _panelOpen = false;
    let _lastCompletedRunId = null;
    let _disabledProps = new Set();
    let _allPropKeys = [];

    function setPanelOpen(open) {
        _panelOpen = open;
        const panel = document.getElementById('sidePanel');
        const main = document.getElementById('mainContent');
        const btn = document.getElementById('sidePanelToggle');
        if (panel) panel.classList.toggle('side-panel-open', open);
        if (main) main.classList.toggle('with-side-panel', open);
        if (btn) btn.textContent = open ? '🗎  Model Checker Results ✕' : '🗎  Model Checker Results';
        localStorage.setItem('mcPanelOpen', open ? '1' : '0');
    }

    function getSafetyGradeHtml(grade) {
        if (!grade) return '';
        const parts = grade.split(',').map(s => s.trim());
        if (parts.length !== 2) return '';
        const us = parts[0].toUpperCase();
        const eu = parseFloat(parts[1]);
        return `<div class="safety-grade">
            <span class="grade-label">Safety Grade:</span>
            <span class="grade-badge grade-us-${us.toLowerCase()}">${us}</span>
            <span class="grade-badge grade-eu-${Math.floor(eu)}">${eu.toFixed(1)}</span>
        </div>`;
    }

    function getDqsHtml(dqs) {
        if (!dqs || typeof dqs !== 'object') return '';
        const score = dqs.dqs;
        const label = (dqs.label || '').toUpperCase();
        const tq = dqs.temporal_quality;
        const vq = dqs.value_quality;
        if (score === undefined && !label) return '';

        const cls = score >= 0.9 ? 'dqs-good'
                  : score >= 0.7 ? 'dqs-acceptable'
                  : score >= 0.5 ? 'dqs-degraded'
                  : score >= 0.3 ? 'dqs-poor'
                  : 'dqs-critical';

        const scoreBadge = score !== undefined
            ? `<span class="grade-badge ${cls}">${(score * 100).toFixed(0)}%</span>`
            : '';
        const labelBadge = label
            ? `<span class="grade-badge ${cls}">${label}</span>`
            : '';
        const tqBadge = tq !== undefined
            ? `<span class="dqs-sub-badge">TQ ${(tq * 100).toFixed(0)}%</span>`
            : '';
        const vqBadge = vq !== undefined
            ? `<span class="dqs-sub-badge">VQ ${(vq * 100).toFixed(0)}%</span>`
            : '';

        return `<div class="safety-grade">
            <span class="grade-label">Data Quality:</span>
            ${scoreBadge}${labelBadge}${tqBadge}${vqBadge}
        </div>`;
    }

    // Keys whose values are large arrays — skip in the stat grid
    const ARRAY_SKIP_KEYS = new Set([
        'speed_values', 'safety_scores', 'acceleration_errors', 'measured_accelerations',
        'commanded_accelerations', 'deceleration_errors', 'measured_decelerations',
        'commanded_decelerations', 'lane_values',
    ]);

    function formatStatValue(v) {
        if (v === null || v === undefined) return null;
        if (Array.isArray(v)) return null;
        if (typeof v === 'object') return null;
        if (typeof v === 'number') {
            // Show integers as-is, floats to 4 sig figs
            return Number.isInteger(v) ? String(v) : v.toPrecision(4);
        }
        return String(v);
    }

    function formatStatKey(k) {
        return k.replace(/_/g, ' ').replace(/\w/g, c => c.toUpperCase());
    }

    function renderStatGrid(obj) {
        if (!obj || typeof obj !== 'object') return '';
        return Object.entries(obj)
            .filter(([k, v]) => !ARRAY_SKIP_KEYS.has(k) && formatStatValue(v) !== null)
            .map(([k, v]) => `<span><strong>${formatStatKey(k)}:</strong> ${formatStatValue(v)}</span>`)
            .join('');
    }

    function propositionHtml(key, prop) {
        const status = (prop.status || 'unknown').toLowerCase();
        const cssClass = { pass: 'proposition-pass', fail: 'proposition-fail', no_data: 'proposition-no-data' }[status] || 'proposition-error';
        const badgeClass = { pass: 'status-pass', fail: 'status-fail', no_data: 'status-no-data' }[status] || 'status-error';
        const desc = prop.description || {};
        const title = desc.title || key.replace(/_/g, ' ');
        const body = desc.description || '';
        const rationale = desc.safety_rationale || '';
        const formulaDesc = prop.formula_description || '';
        const group = (prop.group || '').replace(/_/g, ' ');
        const stats = prop.statistics || {};
        const dqs = prop.dqs || {};
        const isDisabled = _disabledProps.has(key);

        // Top-level scalar fields shown first
        const topRows = [
            ['Formula Type', prop.formula_type],
            ['Logic Type', prop.logic_type],
            ['Threshold', prop.threshold],
            ['States Analyzed', prop.states_analyzed],
            ['Kripke States', prop.kripke_states],
            ['Result', prop.result],
        ].filter(([, v]) => v !== undefined && v !== null)
         .map(([k, v]) => `<span><strong>${k}:</strong> ${formatStatValue(v) ?? String(v)}</span>`)
         .join('');

        const statRows = renderStatGrid(stats);

        const dqsRows = Object.entries(dqs).length
            ? `<div class="prop-stat-section-label">Data Quality</div>` + renderStatGrid(dqs)
            : '';

        return `
        <div class="proposition-item ${cssClass}${isDisabled ? ' proposition-disabled' : ''}" data-prop-key="${key}">
            ${group ? `<div class="group-indicator">${group}</div>` : ''}
            <div class="proposition-header">
                <h4 class="proposition-title">${title}</h4>
                <div style="display:flex;align-items:center;gap:6px;">
                    <span class="proposition-status ${badgeClass}">${status.toUpperCase()}</span>
                    <button class="prop-disable-btn" data-key="${key}" title="${isDisabled ? 'Re-enable proposition' : 'Suppress from violations'}">${isDisabled ? '👁' : '🚫'}</button>
                </div>
            </div>
            ${body ? `<div class="proposition-description">${body}</div>` : ''}
            ${rationale ? `<div class="proposition-rationale"><strong>Why this matters:</strong> ${rationale}</div>` : ''}
            ${formulaDesc ? `<div class="proposition-formula"><strong>Requirement:</strong> ${formulaDesc}</div>` : ''}
            ${getSafetyGradeHtml(stats.safety_grade)}
            ${getDqsHtml(dqs)}
            <div class="proposition-technical">
                <strong>ID:</strong> ${key}
                ${prop.error ? `&nbsp;·&nbsp;<strong>Error:</strong> ${prop.error}` : ''}
                ${topRows ? `<div class="prop-stat-section-label">Parameters</div><div class="prop-stat-grid">${topRows}</div>` : ''}
                ${statRows ? `<div class="prop-stat-section-label">Statistics</div><div class="prop-stat-grid">${statRows}</div>` : ''}
                ${dqsRows ? `<div class="prop-stat-grid">${dqsRows}</div>` : ''}
            </div>
        </div>`;
    }

    function renderResults(results) {
        if (!results) { clearResults(); return; }

        const summary = results.SUMMARY || {};
        const summaryEl = document.getElementById('mcPanelSummary');
        if (summaryEl) {
            const rate = ((summary.success_rate || 0) * 100).toFixed(1);
            summaryEl.innerHTML = `
                <div class="modelcheck-summary">
                    <div class="summary-stat"><span class="value">${summary.total_propositions || 0}</span><span class="label">Total</span></div>
                    <div class="summary-stat"><span class="value">${summary.passed || 0}</span><span class="label">Passed</span></div>
                    <div class="summary-stat"><span class="value">${summary.failed || 0}</span><span class="label">Failed</span></div>
                    <div class="summary-stat rate-stat"><span class="value rate-value">${rate}%</span><span class="label">Rate</span></div>
                    <div class="summary-stat${summary.overall_result === 'PASS' ? ' stat-pass' : summary.overall_result === 'FAIL' ? ' stat-fail' : ''}">
                        <span class="value">${summary.overall_result || '—'}</span><span class="label">Overall</span>
                    </div>
                </div>`;
        }

        const propsEl = document.getElementById('mcPanelPropositions');
        if (propsEl) {
            _allPropKeys = Object.keys(results).filter(k => k !== 'SUMMARY');
            propsEl.innerHTML = _allPropKeys.length
                ? _allPropKeys.map(k => propositionHtml(k, results[k])).join('')
                : '<div style="color:#6c757d;padding:12px;">No proposition results</div>';
            propsEl.querySelectorAll('.prop-disable-btn').forEach(btn => {
                btn.addEventListener('click', e => { e.stopPropagation(); toggleDisabledProp(btn.dataset.key); });
            });
            renderDisabledSection();
        }
    }

    function renderDisabledSection() {
        let el = document.getElementById('mcDisabledSection');
        if (!el) {
            el = document.createElement('div');
            el.id = 'mcDisabledSection';
            document.getElementById('sidePanelBody')?.appendChild(el);
        }
        if (_disabledProps.size === 0) { el.innerHTML = ''; return; }
        el.innerHTML = `<div class="mc-disabled-header">Suppressed Propositions (${_disabledProps.size})</div>` +
            [..._disabledProps].map(k => `
                <div class="mc-disabled-item">
                    <span>${k.replace(/_/g, ' ')}</span>
                    <button class="prop-reenable-btn" data-key="${k}" title="Re-enable">👁 Show</button>
                </div>`).join('');
        el.querySelectorAll('.prop-reenable-btn').forEach(btn => {
            btn.addEventListener('click', () => toggleDisabledProp(btn.dataset.key));
        });
    }

    async function toggleDisabledProp(key) {
        if (_disabledProps.has(key)) _disabledProps.delete(key);
        else _disabledProps.add(key);
        try {
            await fetch('/api/model_checker/continuous/disabled', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ disabled_propositions: [..._disabledProps] }),
            });
        } catch (e) { /* non-fatal */ }
        document.querySelectorAll('[data-prop-key]').forEach(el => {
            const k = el.dataset.propKey;
            el.classList.toggle('proposition-disabled', _disabledProps.has(k));
            const btn = el.querySelector('.prop-disable-btn');
            if (btn) {
                btn.textContent = _disabledProps.has(k) ? '👁' : '🚫';
                btn.title = _disabledProps.has(k) ? 'Re-enable proposition' : 'Suppress from violations';
            }
        });
        renderDisabledSection();
    }

    function clearResults() {
        const s = document.getElementById('mcPanelSummary');
        const p = document.getElementById('mcPanelPropositions');
        if (s) s.innerHTML = '';
        if (p) p.innerHTML = '<div style="color:#6c757d;padding:12px;">No results yet</div>';
    }

    async function pollModelCheck() {
        try {
            const sr = await fetch('/api/scenario/status');
            const ss = await sr.json();

            if (ss.current_model_check_run_id !== undefined && ss.current_model_check_run_id !== null) {
                _runId = ss.current_model_check_run_id;
            }

            const ind = document.getElementById('mcPanelIndicator');
            const txt = document.getElementById('mcPanelStatusText');

            if (_runId !== null && _runId !== undefined) {
                const rr = await fetch(`/api/model_check/result/${_runId}`);
                if (rr.ok) {
                    const data = await rr.json();
                    _status = data.status || 'unknown';
                    if (ind) ind.className = `status-indicator status-${_status}`;
                    if (txt) {
                        let label = _status.toUpperCase() + ` — Run ${_runId}`;
                        if (data.mode) label += ` (${data.mode})`;
                        txt.textContent = label;
                    }
                    if (_status === 'completed' && data.results) {
                        renderResults(data.results);
                        // Only auto-open once per completed run, and only if user has not manually closed
                        if (!_panelOpen && _runId !== _lastCompletedRunId) {
                            _lastCompletedRunId = _runId;
                            if (localStorage.getItem('mcPanelUserClosed') !== '1') setPanelOpen(true);
                        }
                    }
                } else if (rr.status === 404) {
                    _runId = null;
                    _status = 'idle';
                    if (ind) ind.className = 'status-indicator status-idle';
                    if (txt) txt.textContent = 'Idle';
                }
            } else {
                _status = 'idle';
                if (ind) ind.className = 'status-indicator status-idle';
                if (txt) txt.textContent = 'Idle';
            }
        } catch (e) { /* network */ }
    }

    function init() {
        document.getElementById('sidePanelClose')?.addEventListener('click', () => {
            localStorage.setItem('mcPanelUserClosed', '1');
            setPanelOpen(false);
        });
        document.getElementById('sidePanelToggle')?.addEventListener('click', () => {
            const next = !_panelOpen;
            if (next) localStorage.removeItem('mcPanelUserClosed');
            setPanelOpen(next);
        });

        const savedOpen = localStorage.getItem('mcPanelOpen');
        if (savedOpen === '1') setPanelOpen(true);

        clearResults();
        setInterval(pollModelCheck, 2000);
    }

    window.addEventListener('DOMContentLoaded', init);
    window.ModelCheckerPanel = { setPanelOpen, renderResults };
})();
