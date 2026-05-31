// ── Hardware Monitor Panel ────────────────────────────────────────────────────
// Self-contained cluster-aware component. Mount into #hardware-monitor.
// All CSS scoped under #hmp-root. All IDs prefixed hmp-.

(function () {
    'use strict';

    // ── Styles ────────────────────────────────────────────────────────────────
    function injectStyles() {
        if (document.getElementById('hmp-styles')) return;
        const s = document.createElement('style');
        s.id = 'hmp-styles';
        s.textContent = `
#hmp-root {
    display: flex; height: 100%; min-height: 0; overflow: hidden;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 13px; color: #e1e4e8; background: #0f1117;
}
/* ── Left nav ──────────────────────────────────── */
#hmp-nav {
    width: 164px; min-width: 164px; flex-shrink: 0;
    background: #0d1117; border-right: 1px solid #30363d;
    display: flex; flex-direction: column; overflow: hidden;
}
#hmp-host-section {
    border-bottom: 1px solid #30363d; padding: 8px 0 4px;
    flex-shrink: 0;
}
.hmp-nav-section {
    font-size: 10px; font-weight: 600; color: #484f58;
    text-transform: uppercase; letter-spacing: 0.6px;
    padding: 6px 14px 3px; user-select: none;
}
.hmp-host-btn {
    display: flex; align-items: center; gap: 7px;
    width: 100%; background: none; border: none;
    border-left: 2px solid transparent;
    padding: 7px 12px; font-size: 12px; font-weight: 500;
    color: #8b949e; cursor: pointer; text-align: left;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: color .15s, background .15s, border-color .15s;
}
.hmp-host-btn:hover  { color: #c9d1d9; background: #161b22; border-left-color: #30363d; }
.hmp-host-btn.active { color: #58a6ff; background: #161b22; border-left-color: #58a6ff; }
#hmp-view-section { flex: 1; overflow-y: auto; padding: 6px 0; }
.hmp-nav-sep { height: 1px; background: #21262d; margin: 4px 10px; }
.hmp-nav-btn {
    display: block; width: 100%; background: none; border: none;
    border-left: 2px solid transparent; color: #8b949e;
    text-align: left; padding: 7px 12px; font-size: 12px; font-weight: 500;
    cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: color .15s, background .15s, border-color .15s;
}
.hmp-nav-btn:hover  { color: #c9d1d9; background: #161b22; border-left-color: #30363d; }
.hmp-nav-btn.active { color: #58a6ff; background: #161b22; border-left-color: #58a6ff; }
/* ── Body ──────────────────────────────────────── */
#hmp-body {
    flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden;
}
#hmp-topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 7px 14px; background: #161b22; border-bottom: 1px solid #30363d;
    flex-shrink: 0; gap: 10px;
}
#hmp-topbar-title { font-size: 11px; font-weight: 600; color: #6e7681;
                    text-transform: uppercase; letter-spacing: 0.5px; }
#hmp-topbar-right { display: flex; align-items: center; gap: 10px; font-size: 11px; color: #6e7681; }
.hmp-view { display: none; flex: 1; overflow-y: auto; padding: 14px;
            flex-direction: column; gap: 14px; }
.hmp-view.active { display: flex; }
/* ── Dot ───────────────────────────────────────── */
.hmp-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
           background: #6e7681; flex-shrink: 0; }
.hmp-dot.ok    { background: #2ea043; box-shadow: 0 0 5px #2ea04388; }
.hmp-dot.warn  { background: #d29922; box-shadow: 0 0 5px #d2992288;
                 animation: hmp-pulse 1.5s infinite; }
.hmp-dot.error { background: #f85149; box-shadow: 0 0 5px #f8514988;
                 animation: hmp-pulse .8s infinite; }
.hmp-dot.idle  { background: #6e7681; }
.hmp-dot.connecting { background: #58a6ff; animation: hmp-pulse 1s infinite; }
@keyframes hmp-pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
/* ── Cards ─────────────────────────────────────── */
.hmp-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; }
.hmp-card-head { display: flex; align-items: center; justify-content: space-between;
                 margin-bottom: 12px; }
.hmp-card-title { font-size: 11px; font-weight: 600; color: #6e7681;
                  text-transform: uppercase; letter-spacing: 0.5px; }
.hmp-badge { font-size: 10px; padding: 2px 7px; border-radius: 10px;
             background: #21262d; color: #8b949e; border: 1px solid #30363d; white-space: nowrap; }
.hmp-badge.ok    { background: #0d2b12; color: #3fb950; border-color: #2ea04340; }
.hmp-badge.warn  { background: #2b1e00; color: #d29922; border-color: #d2992240; }
.hmp-badge.error { background: #2b0a0a; color: #f85149; border-color: #f8514940; }
/* ── Grids ─────────────────────────────────────── */
.hmp-g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.hmp-g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
.hmp-tiles { display: grid; grid-template-columns: repeat(auto-fill,minmax(145px,1fr)); gap: 10px; }
@media (max-width:900px) { .hmp-g2,.hmp-g3 { grid-template-columns: 1fr; } }
/* ── Cluster overview ──────────────────────────── */
.hmp-cluster-grid {
    display: grid; grid-template-columns: repeat(auto-fill,minmax(260px,1fr)); gap: 12px;
}
.hmp-host-card {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 12px 14px; cursor: pointer; transition: border-color .15s;
}
.hmp-host-card:hover { border-color: #58a6ff; }
.hmp-host-card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.hmp-host-card-name { font-size: 13px; font-weight: 600; color: #c9d1d9; }
.hmp-host-mini-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.hmp-mini-stat { background: #0d1117; border-radius: 4px; padding: 6px 8px; }
.hmp-mini-label { font-size: 10px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.3px; }
.hmp-mini-val { font-size: 14px; font-weight: 700; color: #e1e4e8; }
.hmp-mini-val.ok    { color: #3fb950; }
.hmp-mini-val.warn  { color: #d29922; }
.hmp-mini-val.error { color: #f85149; }
/* ── Metric tile ───────────────────────────────── */
.hmp-tile { background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
            padding: 12px 14px; }
.hmp-tile.warn  { border-color: #d29922; }
.hmp-tile.error { border-color: #f85149; }
.hmp-tile-lbl { font-size: 10px; color: #6e7681; text-transform: uppercase;
                letter-spacing: 0.4px; margin-bottom: 4px; }
.hmp-tile-val { font-size: 20px; font-weight: 700; color: #e1e4e8; line-height: 1.2; }
.hmp-tile-val.ok    { color: #3fb950; }
.hmp-tile-val.warn  { color: #d29922; }
.hmp-tile-val.error { color: #f85149; }
.hmp-tile-sub { font-size: 11px; color: #8b949e; margin-top: 3px; }
/* ── Progress ──────────────────────────────────── */
.hmp-pr { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
.hmp-pr-lbl { font-size: 11px; color: #8b949e; min-width: 72px; }
.hmp-pr-wrap { flex: 1; background: #21262d; border-radius: 3px; height: 7px; overflow: hidden; }
.hmp-pr-bar { height: 100%; border-radius: 3px; transition: width .4s ease; }
.hmp-pr-bar.ok    { background: #2ea043; }
.hmp-pr-bar.warn  { background: #d29922; }
.hmp-pr-bar.error { background: #f85149; }
.hmp-pr-pct { font-size: 11px; min-width: 36px; text-align: right; color: #c9d1d9; }
.hmp-pr-pct.ok    { color: #3fb950; }
.hmp-pr-pct.warn  { color: #d29922; }
.hmp-pr-pct.error { color: #f85149; }
/* ── KV / Table ────────────────────────────────── */
.hmp-kv { width: 100%; border-collapse: collapse; font-size: 12px; }
.hmp-kv td { padding: 5px 8px; border-bottom: 1px solid #1c2128; color: #c9d1d9; }
.hmp-kv td:first-child { color: #6e7681; width: 46%; }
.hmp-kv tr:last-child td { border-bottom: none; }
.hmp-tbl { width: 100%; border-collapse: collapse; font-size: 11px; }
.hmp-tbl th { text-align: left; color: #6e7681; font-size: 10px; font-weight: 600;
              text-transform: uppercase; letter-spacing: 0.4px;
              padding: 5px 8px; border-bottom: 1px solid #21262d; }
.hmp-tbl td { padding: 6px 8px; border-bottom: 1px solid #161b22; color: #c9d1d9; }
.hmp-tbl tr:last-child td { border-bottom: none; }
.hmp-tbl tr:hover td { background: #1c2128; }
/* ── Tags ──────────────────────────────────────── */
.hmp-tag { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px;
           font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; }
.hmp-tag-blue   { background: #1f3a5f; color: #58a6ff; }
.hmp-tag-green  { background: #1a3a1f; color: #3fb950; }
.hmp-tag-yellow { background: #3a2e0a; color: #d29922; }
.hmp-tag-red    { background: #3a1212; color: #f85149; }
.hmp-tag-gray   { background: #21262d; color: #8b949e; }
.hmp-tag-purple { background: #2a1f3a; color: #a371f7; }
/* ── Core grid ─────────────────────────────────── */
.hmp-cores { display: grid; grid-template-columns: repeat(auto-fill,minmax(50px,1fr)); gap: 5px; }
.hmp-core  { background: #0d1117; border: 1px solid #21262d; border-radius: 4px;
             padding: 5px 4px; text-align: center; }
.hmp-core-id  { font-size: 10px; color: #6e7681; }
.hmp-core-pct { font-size: 13px; font-weight: 700; }
/* ── Iface / Device ────────────────────────────── */
.hmp-iface { background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
             padding: 11px 13px; margin-bottom: 8px; }
.hmp-iface-head { display: flex; align-items: center; gap: 7px; margin-bottom: 8px; }
.hmp-iface-name { font-size: 13px; font-weight: 600; color: #c9d1d9; }
.hmp-addr { font-size: 11px; color: #8b949e; font-family: monospace; margin-bottom: 2px; }
.hmp-dev { display: flex; align-items: flex-start; gap: 9px; background: #0d1117;
           border: 1px solid #21262d; border-radius: 6px; padding: 9px 11px; margin-bottom: 6px; }
.hmp-dev-icon { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.hmp-dev-name { font-size: 12px; font-weight: 600; color: #c9d1d9;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hmp-dev-detail { font-size: 11px; color: #8b949e; margin-top: 2px; }
.hmp-dev-tags   { margin-top: 4px; display: flex; gap: 4px; flex-wrap: wrap; }
/* ── Flags / Temps ─────────────────────────────── */
.hmp-flags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.hmp-flag  { font-size: 10px; padding: 1px 6px; border-radius: 3px;
             background: #1f3a5f; color: #58a6ff; font-family: monospace; }
.hmp-temps { display: grid; grid-template-columns: repeat(auto-fill,minmax(130px,1fr)); gap: 8px; }
.hmp-temp  { background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 10px 12px; }
.hmp-temp-name { font-size: 11px; color: #8b949e; margin-bottom: 4px;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hmp-temp-val  { font-size: 20px; font-weight: 700; }
/* ── JSON / Empty ──────────────────────────────── */
.hmp-json { background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
            padding: 11px; font-family: monospace; font-size: 11px; color: #8b949e;
            white-space: pre-wrap; overflow-x: auto; max-height: 500px; overflow-y: auto; }
.hmp-empty { text-align: center; padding: 28px; color: #6e7681; font-size: 12px; }
.hmp-empty-icon { font-size: 28px; margin-bottom: 6px; }
`;
        document.head.appendChild(s);
    }

    // ── Skeleton HTML ─────────────────────────────────────────────────────────
    function buildSkeleton(container) {
        container.innerHTML = `
<div id="hmp-root">
  <nav id="hmp-nav">
    <div id="hmp-host-section">
      <div class="hmp-nav-section">Cluster Hosts</div>
      <div id="hmp-host-list"></div>
    </div>
    <div id="hmp-view-section">
      <div class="hmp-nav-section" style="margin-top:4px">View</div>
      <button class="hmp-nav-btn active" data-view="hmp-v-cluster">Cluster Overview</button>
      <div class="hmp-nav-sep"></div>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-overview">Overview</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-cpu">CPU</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-memory">Memory</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-network">Network</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-storage">Storage</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-gpu">GPU / NPU</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-temps">Temperatures</button>
      <div class="hmp-nav-sep"></div>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-system">System Info</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-pci">PCI Devices</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-usb">USB Devices</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-serial">Serial / UART</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-storage">Block Devices</button>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-inv-sensors">Sensors</button>
      <div class="hmp-nav-sep"></div>
      <button class="hmp-nav-btn hmp-host-required" data-view="hmp-v-raw">Raw JSON</button>
    </div>
  </nav>

  <div id="hmp-body">
    <div id="hmp-topbar">
      <span id="hmp-topbar-title">Hardware Monitor</span>
      <div id="hmp-topbar-right">
        <span class="hmp-dot connecting" id="hmp-dot"></span>
        <span id="hmp-status-txt">Waiting for hosts…</span>
        <span id="hmp-ts" style="font-size:10px;color:#484f58;font-family:monospace"></span>
      </div>
    </div>

    <!-- Cluster overview -->
    <div class="hmp-view active" id="hmp-v-cluster">
      <div class="hmp-cluster-grid" id="hmp-cluster-grid"></div>
    </div>

    <!-- Per-host views (all keyed off _activeHost) -->
    <div class="hmp-view" id="hmp-v-overview">
      <div class="hmp-tiles" id="hmp-ov-tiles"></div>
      <div class="hmp-g2">
        <div class="hmp-card">
          <div class="hmp-card-head"><span class="hmp-card-title">CPU Usage</span>
            <span class="hmp-badge" id="hmp-cpu-badge">—</span></div>
          <div id="hmp-ov-cpu"></div>
        </div>
        <div class="hmp-card">
          <div class="hmp-card-head"><span class="hmp-card-title">Memory</span></div>
          <div id="hmp-ov-ram"></div>
        </div>
      </div>
      <div class="hmp-g2">
        <div class="hmp-card">
          <div class="hmp-card-head"><span class="hmp-card-title">Network</span></div>
          <div id="hmp-ov-net"></div>
        </div>
        <div class="hmp-card">
          <div class="hmp-card-head"><span class="hmp-card-title">Disk Usage</span></div>
          <div id="hmp-ov-disk"></div>
        </div>
      </div>
    </div>

    <div class="hmp-view" id="hmp-v-cpu">
      <div class="hmp-g2">
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Summary</span></div><div id="hmp-cpu-summary"></div></div>
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Load Average</span></div><div id="hmp-cpu-load"></div></div>
      </div>
      <div class="hmp-card">
        <div class="hmp-card-head"><span class="hmp-card-title">Per-Core</span><span class="hmp-badge" id="hmp-core-count">—</span></div>
        <div class="hmp-cores" id="hmp-cores"></div>
      </div>
    </div>

    <div class="hmp-view" id="hmp-v-memory">
      <div class="hmp-g2">
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">RAM</span></div><div id="hmp-ram-detail"></div></div>
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Swap</span></div><div id="hmp-swap-detail"></div></div>
      </div>
    </div>

    <div class="hmp-view" id="hmp-v-network"><div id="hmp-net-cards"></div></div>

    <div class="hmp-view" id="hmp-v-storage">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Mounted Filesystems</span></div><div id="hmp-mounts"></div></div>
      <div class="hmp-card" id="hmp-io-card" style="display:none"><div class="hmp-card-head"><span class="hmp-card-title">I/O Counters</span></div><div id="hmp-io-detail"></div></div>
    </div>

    <div class="hmp-view" id="hmp-v-gpu"><div id="hmp-gpu-cards"></div></div>

    <div class="hmp-view" id="hmp-v-temps">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Sensors</span></div><div class="hmp-temps" id="hmp-temp-grid"></div></div>
    </div>

    <div class="hmp-view" id="hmp-v-inv-system">
      <div class="hmp-g3">
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">System</span></div><div id="hmp-inv-sys-kv"></div></div>
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">CPU</span></div><div id="hmp-inv-cpu-kv"></div></div>
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">RAM</span></div><div id="hmp-inv-ram-kv"></div></div>
      </div>
    </div>

    <div class="hmp-view" id="hmp-v-inv-pci">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">PCI Devices</span></div><div id="hmp-pci-tbl"></div></div>
    </div>
    <div class="hmp-view" id="hmp-v-inv-usb">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">USB Devices</span></div><div id="hmp-usb-list"></div></div>
    </div>
    <div class="hmp-view" id="hmp-v-inv-serial">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Serial / UART</span></div><div id="hmp-serial-list"></div></div>
    </div>
    <div class="hmp-view" id="hmp-v-inv-storage">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Block Devices</span></div><div id="hmp-blk-list"></div></div>
    </div>
    <div class="hmp-view" id="hmp-v-inv-sensors">
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Sensors &amp; Cameras</span></div><div id="hmp-sensor-list"></div></div>
      <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Input &amp; Audio</span></div><div id="hmp-input-list"></div></div>
    </div>

    <div class="hmp-view" id="hmp-v-raw">
      <div class="hmp-g2">
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Hardware Status</span></div><div class="hmp-json" id="hmp-raw-status">—</div></div>
        <div class="hmp-card"><div class="hmp-card-head"><span class="hmp-card-title">Hardware Inventory</span></div><div class="hmp-json" id="hmp-raw-inv">—</div></div>
      </div>
    </div>

  </div>
</div>`;
    }

    // ── State ─────────────────────────────────────────────────────────────────
    let _activeHost = null;
    // {host: {status: obj|null, status_ts: str, inventory: obj|null, inventory_ts: str}}
    const _data = {};

    // ── Helpers ───────────────────────────────────────────────────────────────
    const X = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    function pctCls(p,w=85,e=95){ return p>=e?'error':p>=w?'warn':'ok'; }
    function levelCls(s){ s=String(s||'').toLowerCase(); return s==='ok'?'ok':s==='warn'||s==='warning'?'warn':s==='error'||s==='critical'?'error':''; }
    function prog(label,pct,sub=''){
        const c=pctCls(pct);
        return `<div class="hmp-pr"><span class="hmp-pr-lbl">${X(label)}</span><div class="hmp-pr-wrap"><div class="hmp-pr-bar ${c}" style="width:${Math.min(100,pct)}%"></div></div><span class="hmp-pr-pct ${c}">${pct.toFixed(1)}%</span></div>${sub?`<div style="font-size:10px;color:#6e7681;margin:-3px 0 6px 80px">${X(sub)}</div>`:''}`;
    }
    function kv(rows){ return `<table class="hmp-kv"><tbody>${rows.map(([k,v])=>`<tr><td>${X(k)}</td><td>${X(v)}</td></tr>`).join('')}</tbody></table>`; }
    function tag(t,s='blue'){ return `<span class="hmp-tag hmp-tag-${s}">${X(t)}</span>`; }
    function empty(icon,msg){ return `<div class="hmp-empty"><div class="hmp-empty-icon">${icon}</div>${X(msg)}</div>`; }

    // ── Nav ───────────────────────────────────────────────────────────────────
    function showView(viewId) {
        document.querySelectorAll('#hmp-root .hmp-view').forEach(v => v.classList.remove('active'));
        document.querySelectorAll('#hmp-root .hmp-nav-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(viewId)?.classList.add('active');
        document.querySelector(`.hmp-nav-btn[data-view="${viewId}"]`)?.classList.add('active');
    }

    function bindNav() {
        document.querySelectorAll('#hmp-root .hmp-nav-btn[data-view]').forEach(btn => {
            btn.addEventListener('click', () => {
                const needsHost = btn.classList.contains('hmp-host-required');
                if (needsHost && !_activeHost) return;
                showView(btn.dataset.view);
                if (_activeHost) refreshHostViews();
            });
        });
    }

    // ── Host list in nav ──────────────────────────────────────────────────────
    function refreshHostNav() {
        const el = document.getElementById('hmp-host-list');
        if (!el) return;
        const hosts = Object.keys(_data).sort();
        if (hosts.length === 0) {
            el.innerHTML = `<div style="font-size:11px;color:#484f58;padding:6px 14px">No hosts yet</div>`;
            return;
        }
        el.innerHTML = hosts.map(h => {
            const entry = _data[h];
            const status = entry.status?.status || 'idle';
            const cls = levelCls(status);
            const active = h === _activeHost ? ' active' : '';
            return `<button class="hmp-host-btn${active}" data-host="${X(h)}">
                <span class="hmp-dot ${cls}"></span>
                <span style="overflow:hidden;text-overflow:ellipsis">${X(h)}</span>
            </button>`;
        }).join('');
        el.querySelectorAll('.hmp-host-btn').forEach(btn => {
            btn.addEventListener('click', () => selectHost(btn.dataset.host));
        });
    }

    function selectHost(host) {
        _activeHost = host;
        refreshHostNav();
        // Update topbar
        const entry = _data[host] || {};
        const s = entry.status;
        const dot = document.getElementById('hmp-dot');
        const txt = document.getElementById('hmp-status-txt');
        const ts  = document.getElementById('hmp-ts');
        if (dot) dot.className = `hmp-dot ${levelCls(s?.status)||'idle'}`;
        if (txt) txt.textContent = `${host} — ${(s?.status||'—').toUpperCase()}`;
        if (ts && entry.status_ts) ts.textContent = entry.status_ts.slice(11,19)+' UTC';
        // Switch to overview if currently on cluster view
        const activeView = document.querySelector('#hmp-root .hmp-view.active');
        if (!activeView || activeView.id === 'hmp-v-cluster') showView('hmp-v-overview');
        refreshHostViews();
    }

    // ── Cluster overview ──────────────────────────────────────────────────────
    function renderClusterOverview() {
        const el = document.getElementById('hmp-cluster-grid');
        if (!el) return;
        const hosts = Object.keys(_data).sort();
        if (hosts.length === 0) {
            el.innerHTML = empty('🖥', 'No cluster hosts detected yet.\nWaiting for hardware_monitor nodes to publish…');
            return;
        }
        el.innerHTML = hosts.map(h => {
            const s = _data[h].status || {};
            const cpu = s.cpu || {};
            const ram = s.ram || {};
            const net = s.network || {};
            const overallCls = levelCls(s.status);
            const ifaceCount = Object.keys(net.interfaces || {}).length;
            const firstIface = Object.values(net.interfaces || {})[0];
            const firstIp = firstIface?.ipv4?.[0] || '—';
            return `<div class="hmp-host-card" data-host="${X(h)}">
                <div class="hmp-host-card-head">
                    <span class="hmp-dot ${overallCls || 'idle'}"></span>
                    <span class="hmp-host-card-name">${X(h)}</span>
                    <span style="margin-left:auto">${tag((s.status||'—').toUpperCase(), overallCls||'gray')}</span>
                </div>
                <div class="hmp-host-mini-stats">
                    <div class="hmp-mini-stat">
                        <div class="hmp-mini-label">CPU</div>
                        <div class="hmp-mini-val ${pctCls(cpu.overall_percent??0)}">${(cpu.overall_percent??0).toFixed(0)}%</div>
                    </div>
                    <div class="hmp-mini-stat">
                        <div class="hmp-mini-label">RAM</div>
                        <div class="hmp-mini-val ${pctCls(ram.used_percent??0)}">${(ram.used_percent??0).toFixed(0)}%</div>
                    </div>
                    <div class="hmp-mini-stat">
                        <div class="hmp-mini-label">Load</div>
                        <div class="hmp-mini-val">${(cpu.load_avg?.['1m']??0).toFixed(2)}</div>
                    </div>
                    <div class="hmp-mini-stat">
                        <div class="hmp-mini-label">IP</div>
                        <div class="hmp-mini-val" style="font-size:10px;font-family:monospace">${X(firstIp)}</div>
                    </div>
                </div>
            </div>`;
        }).join('');
        el.querySelectorAll('.hmp-host-card').forEach(c => {
            c.addEventListener('click', () => selectHost(c.dataset.host));
        });
    }

    // ── Per-host status views ─────────────────────────────────────────────────
    function refreshHostViews() {
        if (!_activeHost) return;
        const entry = _data[_activeHost] || {};
        const s = entry.status;
        const inv = entry.inventory;
        if (s) {
            renderOverview(s);
            renderCpuView(s.cpu);
            renderMemoryView(s.ram);
            renderNetworkView(s.network);
            renderStorageView(s.disk);
            renderGpuView(s.gpu);
            renderTempsView(s.temperatures);
            document.getElementById('hmp-raw-status').textContent = JSON.stringify(s, null, 2);
        }
        if (inv) {
            renderInventory(inv);
            document.getElementById('hmp-raw-inv').textContent = JSON.stringify(inv, null, 2);
        }
    }

    function renderOverview(s) {
        const cpu=s.cpu||{}, ram=s.ram||{}, net=s.network||{}, ntp=s.ntp||{}, proc=s.processes||{};
        document.getElementById('hmp-ov-tiles').innerHTML = [
            {l:'Hostname', v:X(s.hostname||'—'), sub:'', c:''},
            {l:'CPU', v:`${(cpu.overall_percent??0).toFixed(1)}%`, sub:`load ${(cpu.load_avg?.['1m']??0).toFixed(2)}`, c:pctCls(cpu.overall_percent??0)},
            {l:'RAM', v:`${(ram.used_percent??0).toFixed(1)}%`, sub:`${ram.used_mb??0}/${ram.total_mb??0} MB`, c:pctCls(ram.used_percent??0)},
            {l:'Processes', v:proc.total??'—', sub:`${proc.running??0} running`, c:(proc.zombie??0)>5?'warn':''},
            {l:'NTP', v:ntp.synchronized===false?'UNSYNC':ntp.synchronized===true?'SYNC':'—', sub:ntp.source||'', c:ntp.synchronized===false?'warn':'ok'},
            {l:'Status', v:(s.status||'—').toUpperCase(), sub:'', c:levelCls(s.status)},
        ].map(t=>`<div class="hmp-tile ${t.c}"><div class="hmp-tile-lbl">${t.l}</div><div class="hmp-tile-val ${t.c}">${t.v}</div>${t.sub?`<div class="hmp-tile-sub">${t.sub}</div>`:''}</div>`).join('');

        const pct=cpu.overall_percent??0;
        document.getElementById('hmp-cpu-badge').textContent=`${pct.toFixed(1)}%`;
        document.getElementById('hmp-ov-cpu').innerHTML=
            prog('Overall',pct)+(cpu.per_core_percent||[]).slice(0,6).map((p,i)=>prog(`Core ${i}`,p)).join('');

        const swap=ram.swap||{};
        document.getElementById('hmp-ov-ram').innerHTML=
            prog('Used',ram.used_percent??0,`${ram.used_mb??0}/${ram.total_mb??0} MB`)+
            (swap.total_mb>0?prog('Swap',swap.used_percent??0,`${swap.used_mb??0}/${swap.total_mb??0} MB`):'');

        document.getElementById('hmp-ov-net').innerHTML=
            Object.entries(net.interfaces||{}).map(([nm,iface])=>{
                const up=iface.is_up;
                return `<div class="hmp-iface"><div class="hmp-iface-head">
                    <span class="hmp-dot ${up?'ok':'error'}"></span>
                    <span class="hmp-iface-name">${X(nm)}</span>
                    ${tag(up?'UP':'DOWN',up?'green':'red')}
                    ${iface.type?tag(iface.type,'blue'):''}
                </div>
                <div class="hmp-addr">🌐 ${X((iface.ipv4||[]).join(', ')||'no address')}</div>
                ${iface.mac?`<div class="hmp-addr">⊟ ${X(iface.mac)}</div>`:''}
                </div>`;
            }).join('')||empty('📡','No interfaces');

        document.getElementById('hmp-ov-disk').innerHTML=
            Object.entries((s.disk||{}).mounts||{}).slice(0,6)
                .map(([mp,m])=>prog(mp,m.used_percent??0,`${m.used_gb}/${m.total_gb} GB · ${m.fstype||''}`))
                .join('')||empty('💾','No mounts');
    }

    function renderCpuView(cpu) {
        if (!cpu) return;
        document.getElementById('hmp-cpu-summary').innerHTML=kv([
            ['Overall %',`${(cpu.overall_percent??0).toFixed(1)}%`],
            ['Frequency', cpu.freq_mhz?`${cpu.freq_mhz} MHz`:'—'],
            ['Status', (cpu.status||'—').toUpperCase()],
        ]);
        const la=cpu.load_avg||{};
        document.getElementById('hmp-cpu-load').innerHTML=kv([['1 min',la['1m']??'—'],['5 min',la['5m']??'—'],['15 min',la['15m']??'—']]);
        const cores=cpu.per_core_percent||[];
        document.getElementById('hmp-core-count').textContent=`${cores.length} cores`;
        document.getElementById('hmp-cores').innerHTML=
            cores.map((p,i)=>`<div class="hmp-core"><div class="hmp-core-id">C${i}</div><div class="hmp-core-pct ${pctCls(p)}">${p.toFixed(0)}%</div></div>`).join('')
            ||empty('⚙','No data');
    }

    function renderMemoryView(ram) {
        if (!ram) return;
        document.getElementById('hmp-ram-detail').innerHTML=
            prog('Used',ram.used_percent??0)+kv([['Total',`${ram.total_mb??0} MB`],['Used',`${ram.used_mb??0} MB`],['Available',`${ram.available_mb??0} MB`]]);
        const swap=ram.swap||{};
        document.getElementById('hmp-swap-detail').innerHTML=
            (swap.total_mb>0?prog('Used',swap.used_percent??0):'')+kv([['Total',`${swap.total_mb??0} MB`],['Used',`${swap.used_mb??0} MB`]]);
    }

    function renderNetworkView(net) {
        if (!net) return;
        document.getElementById('hmp-net-cards').innerHTML=
            Object.entries(net.interfaces||{}).map(([nm,iface])=>{
                const up=iface.is_up, io=iface.io||{};
                const addrs=[...(iface.ipv4||[]),...(iface.ipv6||[])];
                return `<div class="hmp-card" style="margin-bottom:12px">
                    <div class="hmp-card-head">
                        <div style="display:flex;align-items:center;gap:7px">
                            <span class="hmp-dot ${up?'ok':'error'}"></span>
                            <span class="hmp-card-title">${X(nm)}</span>
                            ${tag(up?'UP':'DOWN',up?'green':'red')}
                            ${iface.type?tag(iface.type,'blue'):''}
                        </div>
                        ${iface.driver?`<span class="hmp-badge">${X(iface.driver)}</span>`:''}
                    </div>
                    <div class="hmp-g2">
                        <div>${kv([['MAC',iface.mac||'—'],['MTU',iface.mtu||'—'],['Speed',iface.speed_mbps?`${iface.speed_mbps} Mbps`:'—'],['Duplex',iface.duplex||'—'],['State',iface.operstate||'—']])}</div>
                        <div>${addrs.map(a=>`<div class="hmp-addr" style="margin-bottom:4px">${X(a)}</div>`).join('')||empty('🌐','No addresses')}</div>
                    </div>
                    ${Object.keys(io).length?`<div style="margin-top:8px">${kv([['Sent',`${io.bytes_sent_mb??0} MB`],['Received',`${io.bytes_recv_mb??0} MB`],['Errors',`${io.errors_in??0} in / ${io.errors_out??0} out`],['Drops',`${io.drops_in??0} in / ${io.drops_out??0} out`]])}</div>`:''}
                </div>`;
            }).join('')||empty('📡','No network data');
    }

    function renderStorageView(disk) {
        if (!disk) return;
        document.getElementById('hmp-mounts').innerHTML=
            `<table class="hmp-tbl"><thead><tr><th>Mount</th><th>Type</th><th>Total</th><th>Used</th><th>Free</th><th>%</th></tr></thead><tbody>`+
            Object.entries(disk.mounts||{}).map(([mp,m])=>`<tr><td style="font-family:monospace">${X(mp)}</td><td>${tag(m.fstype||'?','gray')}</td><td>${m.total_gb} GB</td><td>${m.used_gb} GB</td><td>${m.free_gb} GB</td><td class="${pctCls(m.used_percent??0)}">${(m.used_percent??0).toFixed(1)}%</td></tr>`).join('')+
            `</tbody></table>`||empty('💾','No mounts');
        const io=disk.io, ioCard=document.getElementById('hmp-io-card');
        if (io) { ioCard.style.display=''; document.getElementById('hmp-io-detail').innerHTML=kv([['Total Read',`${io.total_read_mb} MB`],['Total Write',`${io.total_write_mb} MB`],['Read Count',io.read_count],['Write Count',io.write_count]]); }
        else ioCard.style.display='none';
    }

    function renderGpuView(gpuList) {
        const el=document.getElementById('hmp-gpu-cards');
        if (!gpuList||!gpuList.length){el.innerHTML=empty('🎮','No GPU / NPU detected');return;}
        el.innerHTML=gpuList.map(gpu=>`
            <div class="hmp-card" style="margin-bottom:12px">
                <div class="hmp-card-head">
                    <div style="display:flex;align-items:center;gap:7px"><span class="hmp-card-title">${X(gpu.name||'GPU')}</span>${tag(gpu.vendor||'?','purple')} ${tag(gpu.type||'GPU','blue')}</div>
                    <span class="hmp-badge ${levelCls(gpu.status)}">${(gpu.status||'—').toUpperCase()}</span>
                </div>
                ${gpu.utilization_percent!==undefined?prog('GPU',gpu.utilization_percent):''}
                ${gpu.memory_utilization_percent!==undefined?prog('VRAM',gpu.memory_utilization_percent):''}
                ${kv([...(gpu.temperature_celsius!==undefined?[['Temperature',`${gpu.temperature_celsius} °C`]]:[]),...(gpu.memory_used_mb?[['VRAM Used',`${gpu.memory_used_mb}/${gpu.memory_total_mb} MB`]]:[]),...(gpu.power_draw_w?[['Power',`${gpu.power_draw_w} W`]]:[])],)}
            </div>`).join('');
    }

    function renderTempsView(temps) {
        const el=document.getElementById('hmp-temp-grid');
        if (!temps||!temps.sensors||!Object.keys(temps.sensors).length){el.innerHTML=empty('🌡','No data');return;}
        const cells=[];
        for (const [chip,readings] of Object.entries(temps.sensors)) {
            if (readings?.celsius!==undefined) {
                const c=pctCls(readings.celsius,70,85);
                cells.push(`<div class="hmp-temp"><div class="hmp-temp-name">${X(chip)}</div><div class="hmp-temp-val ${c}">${readings.celsius}°C</div></div>`);
            } else if (typeof readings==='object') {
                for (const [label,r] of Object.entries(readings)) {
                    if (r?.celsius!==undefined) {
                        const c=pctCls(r.celsius,70,85);
                        cells.push(`<div class="hmp-temp"><div class="hmp-temp-name">${X(chip)}/${X(label)}</div><div class="hmp-temp-val ${c}">${r.celsius}°C</div>${r.critical?`<div style="font-size:10px;color:#6e7681">crit ${r.critical}°C</div>`:''}</div>`);
                    }
                }
            }
        }
        el.innerHTML=cells.join('')||empty('🌡','No readings');
    }

    function renderInventory(inv) {
        if (!inv) return;
        const sys=inv.system||{}, cpu=inv.cpu||{}, ram=inv.ram||{};
        document.getElementById('hmp-inv-sys-kv').innerHTML=kv([['Hostname',inv.hostname||'—'],['OS',sys.os||'—'],['Kernel',sys.kernel||'—'],['Architecture',sys.machine||'—']]);
        document.getElementById('hmp-inv-cpu-kv').innerHTML=
            kv([['Model',cpu.model||'—'],['Architecture',cpu.architecture||'—'],['Physical Cores',cpu.physical_cores||'—'],['Logical Cores',cpu.logical_cores||'—'],['Max Freq',cpu.base_frequency_mhz?`${cpu.base_frequency_mhz} MHz`:'—'],['L1d Cache',cpu.cache?.l1d_kb?`${cpu.cache.l1d_kb} KB`:'—'],['L2 Cache',cpu.cache?.l2_kb?`${cpu.cache.l2_kb} KB`:'—'],['L3 Cache',cpu.cache?.l3_kb?`${cpu.cache.l3_kb} KB`:'—']])+
            (cpu.flags?.length?`<div class="hmp-flags">${cpu.flags.map(f=>`<span class="hmp-flag">${X(f)}</span>`).join('')}</div>`:'');
        document.getElementById('hmp-inv-ram-kv').innerHTML=
            kv([['Total',`${ram.total_mb||0} MB`],['NUMA Nodes',(ram.numa_nodes||[]).length]])+
            (ram.numa_nodes||[]).map(n=>`<div style="font-size:11px;color:#8b949e;margin-top:4px">Node ${n.node}: ${n.total_mb} MB · CPUs ${n.cpus}</div>`).join('');
        const pci=inv.pci||[];
        document.getElementById('hmp-pci-tbl').innerHTML=pci.length
            ?`<table class="hmp-tbl"><thead><tr><th>Slot</th><th>Class</th><th>IDs</th><th>Driver</th></tr></thead><tbody>${pci.map(d=>`<tr><td style="font-family:monospace;font-size:10px">${X(d.slot)}</td><td>${tag(d.subclass_label||d.class_label||'?','gray')}</td><td style="font-family:monospace;font-size:10px">${X(d.vendor_id)}:${X(d.device_id)}</td><td>${d.driver?tag(d.driver,'blue'):''}</td></tr>`).join('')}</tbody></table>`
            :empty('🔌','No PCI devices');
        const usb=inv.usb||[];
        document.getElementById('hmp-usb-list').innerHTML=usb.length
            ?usb.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">🔌</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.product||d.id||'USB Device')}</div><div class="hmp-dev-detail">${X(d.manufacturer||'')} · ${X(d.id)} · USB ${X(d.usb_version||'?')} · ${X(d.speed_mbps||'?')} Mbps</div><div class="hmp-dev-tags">${tag(d.class_label||'?','gray')}${(d.drivers||[]).map(dr=>tag(dr,'blue')).join('')}${d.serial?`<span style="font-size:10px;color:#6e7681;font-family:monospace">${X(d.serial)}</span>`:''}</div></div></div>`).join('')
            :empty('🔌','No USB devices');
        const serial=inv.serial||[];
        document.getElementById('hmp-serial-list').innerHTML=serial.length
            ?serial.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">📡</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.device)}</div><div class="hmp-dev-detail">${X(d.type)} · driver: ${X(d.driver||'—')}</div>${d.uart_type?`<div class="hmp-dev-detail">UART ${X(d.uart_type)} · 0x${X(d.port_address||'?')} · IRQ ${X(d.irq||'?')}</div>`:''}${d.usb_manufacturer?`<div class="hmp-dev-detail">USB: ${X(d.usb_manufacturer)} ${X(d.usb_product||'')}</div>`:''}${d.is_console?tag('console','yellow'):''}</div></div>`).join('')
            :empty('📡','No serial ports');
        const stor=inv.storage||[];
        document.getElementById('hmp-blk-list').innerHTML=stor.length
            ?stor.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">💾</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.device)} ${X(d.size)}</div><div class="hmp-dev-detail">${X(d.model||'—')} · ${X(d.vendor||'—')}</div><div class="hmp-dev-tags">${tag(d.type,'blue')} ${d.transport?tag(d.transport,'gray'):''}${d.serial?`<span style="font-size:10px;color:#6e7681;font-family:monospace">${X(d.serial)}</span>`:''}</div><div class="hmp-dev-detail">${d.partitions} partition(s) · ${d.logical_sector_bytes||512}B sectors</div></div></div>`).join('')
            :empty('💾','No block devices');
        const sensors=inv.sensors||[];
        document.getElementById('hmp-sensor-list').innerHTML=sensors.length
            ?sensors.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">📷</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.name)}</div><div class="hmp-dev-tags">${tag(d.type,'blue')} ${tag(d.interface,'gray')}</div>${d.device?`<div class="hmp-dev-detail">${X(d.device)}</div>`:''}</div></div>`).join('')
            :empty('📷','No sensors');
        const audio=inv.audio||[], inputs=inv.input||[];
        document.getElementById('hmp-input-list').innerHTML=[
            ...audio.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">🔊</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.name||d.description)}</div><div class="hmp-dev-detail">${X(d.description||'')} · card ${d.card_index}</div></div></div>`),
            ...inputs.map(d=>`<div class="hmp-dev"><div class="hmp-dev-icon">⌨</div><div style="min-width:0"><div class="hmp-dev-name">${X(d.name)}</div><div class="hmp-dev-tags">${tag(d.type,'gray')}</div>${d.phys?`<div class="hmp-dev-detail">${X(d.phys)}</div>`:''}</div></div>`),
        ].join('')||empty('⌨','No input/audio');
    }

    // ── Data fetching ─────────────────────────────────────────────────────────
    let _sse = null;

    function connectSSE() {
        if (_sse) { _sse.close(); _sse = null; }
        _sse = new EventSource('/api/hardware/stream');
        _sse.onmessage = e => {
            try {
                const p = JSON.parse(e.data);
                const host = p.host;
                if (!host) return;
                if (!_data[host]) _data[host] = {status:null,status_ts:null,inventory:null,inventory_ts:null};
                _data[host].status    = p.data;
                _data[host].status_ts = p.received_at;
                refreshHostNav();
                renderClusterOverview();
                if (_activeHost === host) {
                    // Update topbar
                    const dot=document.getElementById('hmp-dot');
                    const txt=document.getElementById('hmp-status-txt');
                    const ts =document.getElementById('hmp-ts');
                    if(dot) dot.className=`hmp-dot ${levelCls(p.data?.status)||'idle'}`;
                    if(txt) txt.textContent=`${host} — ${(p.data?.status||'—').toUpperCase()}`;
                    if(ts && p.received_at) ts.textContent=p.received_at.slice(11,19)+' UTC';
                    refreshHostViews();
                }
            } catch (_) {}
        };
        _sse.onerror = () => {
            document.getElementById('hmp-dot')?.setAttribute('class','hmp-dot idle');
            document.getElementById('hmp-status-txt').textContent = 'Reconnecting…';
            _sse.close(); _sse = null;
            setTimeout(connectSSE, 4000);
        };
        _sse.onopen = () => {
            document.getElementById('hmp-status-txt').textContent =
                _activeHost ? `${_activeHost} — connected` : 'Connected — waiting for hosts…';
        };
    }

    async function pollHosts() {
        try {
            const r = await fetch('/api/hardware/hosts');
            if (!r.ok) return;
            const d = await r.json();
            for (const [host, meta] of Object.entries(d.hosts || {})) {
                if (!_data[host]) _data[host] = {status:null,status_ts:null,inventory:null,inventory_ts:null};
                // Fetch inventory for new hosts or stale ones
                if (meta.inventory_available && !_data[host].inventory) {
                    fetch(`/api/hardware/hosts/${host}/inventory`)
                        .then(r => r.ok ? r.json() : null)
                        .then(d => {
                            if (d?.available) {
                                _data[host].inventory    = d.data;
                                _data[host].inventory_ts = d.received_at;
                                if (_activeHost === host) refreshHostViews();
                            }
                        }).catch(() => {});
                }
            }
            refreshHostNav();
            renderClusterOverview();
        } catch (_) {}
    }

    // ── Public API ────────────────────────────────────────────────────────────
    function init() {
        const container = document.getElementById('hardware-monitor');
        if (!container || document.getElementById('hmp-root')) return;
        injectStyles();
        buildSkeleton(container);
        bindNav();
        connectSSE();
        pollHosts();
        setInterval(pollHosts, 10000);
    }

    window.HardwareMonitorPanel = { init };

    window.addEventListener('tabchange', e => {
        if (e.detail.tab === 'hardware-monitor') {
            if (!document.getElementById('hmp-root')) init();
        }
    });

    window.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('hardware-monitor')?.classList.contains('active')) init();
    });
})();
