// ── Tab management ────────────────────────────────────────────────────────────
(function () {
    'use strict';

    let _mcFrameLoaded = false;
    let _vizFrameLoaded = false;

    function showTab(name) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        const btn = document.querySelector(`.tab[data-tab="${name}"]`);
        const panel = document.getElementById(name);
        if (btn) btn.classList.add('active');
        if (panel) panel.classList.add('active');

        if (name === 'model-checker' && !_mcFrameLoaded) {
            const frame = document.getElementById('modelCheckerFrame');
            if (frame && frame.dataset.src) {
                frame.src = frame.dataset.src;
                _mcFrameLoaded = true;
            }
        }

        if (name === 'visualization' && !_vizFrameLoaded) {
            const frame = document.getElementById('lichtblickFrame');
            if (frame && frame.dataset.src) {
                frame.src = frame.dataset.src;
                _vizFrameLoaded = true;
            }
        }

        window.dispatchEvent(new CustomEvent('tabchange', { detail: { tab: name } }));
    }

    function initTabs() {
        document.querySelectorAll('.tab[data-tab]').forEach(btn => {
            btn.addEventListener('click', () => showTab(btn.dataset.tab));
        });

        document.querySelectorAll('.log-tab[data-logtab]').forEach(btn => {
            btn.addEventListener('click', () => {
                const parent = btn.closest('.split-right, .control-panel, .tab-content');
                parent.querySelectorAll('.log-tab').forEach(t => t.classList.remove('active'));
                parent.querySelectorAll('.log-tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                const target = document.getElementById(btn.dataset.logtab);
                if (target) target.classList.add('active');
            });
        });
    }

    window.showTab = showTab;
    window.addEventListener('DOMContentLoaded', initTabs);
})();
