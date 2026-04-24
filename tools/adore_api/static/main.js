// ── Bootstrap ─────────────────────────────────────────────────────────────────
(function () {
    'use strict';

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function markdownToHtml(md) {
        return md
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/```json\n([\s\S]*?)```/g, '<div class="api-endpoint"><pre><code>$1</code></pre></div>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.+)$/gm, (_, line) =>
                /^(<h[1-6]|<pre|<ul|<li|<div|<\/|<p)/.test(line.trim()) ? line : `<p>${line}</p>`)
            .replace(/<p><\/p>/g, '')
            .replace(/<strong>GET<\/strong>/g, '<span class="api-method method-get">GET</span>')
            .replace(/<strong>POST<\/strong>/g, '<span class="api-method method-post">POST</span>')
            .replace(/<strong>DELETE<\/strong>/g, '<span class="api-method method-delete">DELETE</span>')
            .replace(/<code>\/api\/([^<]+)<\/code>/g, '<span class="api-url">/api/$1</span>');
    }

    async function loadApiReference() {
        const loading = document.getElementById('api-reference-loading');
        const content = document.getElementById('api-reference-content');
        try {
            const r = await fetch('/api_reference.md');
            const text = await r.text();
            if (content) { content.innerHTML = markdownToHtml(text); content.style.display = 'block'; }
            if (loading) loading.style.display = 'none';
        } catch (e) {
            if (loading) loading.innerHTML = '<p style="color:#dc3545;">Failed to load API reference.</p>';
        }
    }

    function init() {
        // Wire lichtblick URL enter key
        document.getElementById('lichtblickUrl')?.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                document.getElementById('lichtblickFrame').src = e.target.value;
            }
        });

        // Load API reference lazily
        window.addEventListener('tabchange', e => {
            if (e.detail.tab === 'api-reference') loadApiReference();
        });
    }

    window.addEventListener('DOMContentLoaded', init);
})();
