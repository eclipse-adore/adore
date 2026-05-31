// ── Fuzzy scenario finder ─────────────────────────────────────────────────────
(function () {
    'use strict';

    let _scenarios = [];
    let _selected = '';

    function fuzzyScore(query, str) {
        if (!query) return 1;
        const q = query.toLowerCase();
        const s = str.toLowerCase();

        // Exact substring match gets highest priority
        if (s.includes(q)) return 1000 - s.indexOf(q);

        // Character-order match (fuzzy)
        let qi = 0;
        let score = 0;
        let consecutive = 0;
        for (let si = 0; si < s.length && qi < q.length; si++) {
            if (s[si] === q[qi]) {
                score += 1 + consecutive * 2;
                consecutive++;
                qi++;
            } else {
                consecutive = 0;
            }
        }
        return qi === q.length ? score : -1;
    }

    function highlightMatch(query, str) {
        if (!query) return escapeHtml(str);
        const q = query.toLowerCase();
        const s = str.toLowerCase();

        // Try substring highlight first
        const idx = s.indexOf(q);
        if (idx >= 0) {
            return escapeHtml(str.slice(0, idx))
                + '<mark>' + escapeHtml(str.slice(idx, idx + q.length)) + '</mark>'
                + escapeHtml(str.slice(idx + q.length));
        }

        // Fuzzy character highlight
        let result = '';
        let qi = 0;
        for (let si = 0; si < str.length; si++) {
            if (qi < q.length && s[si] === q[qi]) {
                result += '<mark>' + escapeHtml(str[si]) + '</mark>';
                qi++;
            } else {
                result += escapeHtml(str[si]);
            }
        }
        return result;
    }

    function escapeHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function renderList(query) {
        const list = document.getElementById('fuzzyList');
        if (!list) return;

        const scored = _scenarios
            .map(s => ({ s, score: fuzzyScore(query, s) }))
            .filter(x => x.score > 0)
            .sort((a, b) => b.score - a.score);

        if (scored.length === 0) {
            list.innerHTML = '<div class="fuzzy-item fuzzy-empty">No scenarios match</div>';
            list.style.display = 'block';
            return;
        }

        list.innerHTML = scored.slice(0, 80).map(({ s }) => `
            <div class="fuzzy-item${s === _selected ? ' fuzzy-selected' : ''}"
                 data-path="${escapeHtml(s)}" title="${escapeHtml(s)}">
                <span class="fuzzy-item-name">${highlightMatch(query, s.split('/').pop())}</span>
                <span class="fuzzy-item-dir">${escapeHtml(s.includes('/') ? s.slice(0, s.lastIndexOf('/') + 1) : '')}</span>
            </div>
        `).join('');

        list.querySelectorAll('.fuzzy-item[data-path]').forEach(el => {
            el.addEventListener('click', () => selectScenario(el.dataset.path));
        });

        list.style.display = 'block';
    }

    function selectScenario(path) {
        _selected = path;
        const input = document.getElementById('scenarioSearchInput');
        if (input) input.value = path;

        const display = document.getElementById('selectedScenarioName');
        if (display) display.textContent = path || '— none —';

        const list = document.getElementById('fuzzyList');
        if (list) list.style.display = 'none';

        window.dispatchEvent(new CustomEvent('scenarioselected', { detail: { path } }));
    }

    function getSelectedScenario() { return _selected; }

    function setScenarios(scenarios) {
        _scenarios = scenarios || [];
        renderList('');
    }

    function initFuzzyFinder() {
        const input = document.getElementById('scenarioSearchInput');
        const clear = document.getElementById('fuzzySearchClear');
        const list = document.getElementById('fuzzyList');
        if (!input || !list) return;

        input.addEventListener('input', () => renderList(input.value.trim()));
        input.addEventListener('focus', () => {
            renderList(input.value.trim());
            list.style.display = 'block';
        });
        input.addEventListener('keydown', e => {
            if (e.key === 'Escape') { list.style.display = 'none'; input.blur(); }
        });

        if (clear) {
            clear.addEventListener('click', () => {
                input.value = '';
                renderList('');
                input.focus();
            });
        }

        document.addEventListener('click', e => {
            if (!e.target.closest('#fuzzyFinder')) {
                if (list) list.style.display = 'none';
            }
        });
    }

    window.FuzzyFinder = { init: initFuzzyFinder, setScenarios, getSelectedScenario, selectScenario };
    window.addEventListener('DOMContentLoaded', initFuzzyFinder);
})();
