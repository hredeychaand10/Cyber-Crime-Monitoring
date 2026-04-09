const $ = id => document.getElementById(id);

function esc(s) {
    return String(s)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

const counts = { total: 0, critical: 0, high: 0, medium: 0 };

function bumpStats(level) {
    counts.total++;
    if (level in counts) counts[level]++;
    $("stat-total").textContent    = counts.total;
    $("stat-critical").textContent = counts.critical;
    $("stat-high").textContent     = counts.high;
    $("stat-medium").textContent   = counts.medium;
}

function addAlert(msg, prepend = false) {
    const list = $("alert-list");
    const empty = list.querySelector(".empty-admin");
    if (empty) empty.remove();

    const { sender, content, timestamp, analysis: a } = msg;
    bumpStats(a.risk_level);

    const cats = a.categories.map(c => `<span class="tag">${esc(c)}</span>`).join("");
    const pats = a.matched_patterns.map(p => `<span class="tag" style="color:var(--text-muted)">${esc(p)}</span>`).join("");

    const card = document.createElement("div");
    card.className = `alert-card risk-${a.risk_level}`;
    card.innerHTML = `
        <div class="alert-header">
            <span class="alert-sender">${esc(sender)}</span>
            <div class="alert-meta">
                <span class="risk-badge badge-${a.risk_level}">${a.risk_level.toUpperCase()}</span>
                <span class="score-chip">score&nbsp;${a.risk_score}</span>
                <span class="alert-time">${esc(timestamp)}</span>
            </div>
        </div>
        <div class="alert-body">"${esc(content)}"</div>
        <div class="alert-tags">${cats}${pats}</div>`;

    if (prepend && list.firstChild) {
        list.insertBefore(card, list.firstChild);
    } else {
        list.appendChild(card);
    }
}

function showToast(msg) {
    const a = msg.analysis;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
        <div class="toast-title">⚠ ${esc(a.risk_level.toUpperCase())} — ${esc(msg.sender)}</div>
        <div class="toast-body">${esc(msg.content.length > 70 ? msg.content.slice(0, 70) + "…" : msg.content)}</div>`;

    $("toast-container").appendChild(toast);
    setTimeout(() => toast.remove(), 5000);

    try {
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = "sine";
        osc.frequency.value = 520;
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
    } catch (_) {}
}

function connect() {
    const dot = $("conn-dot");
    const label = $("conn-label");

    dot.className = "conn-dot";
    label.textContent = "Connecting…";

    const es = new EventSource("/admin/stream");

    es.onopen = () => {
        dot.className = "conn-dot";
        label.textContent = "Live";
    };

    es.onmessage = e => {
        const msg = JSON.parse(e.data);
        addAlert(msg, true);
        showToast(msg);
    };

    es.onerror = () => {
        dot.className = "conn-dot error";
        label.textContent = "Reconnecting…";
        es.close();
        setTimeout(connect, 3000);
    };
}

fetch("/admin/flagged")
    .then(r => r.json())
    .then(msgs => msgs.forEach(m => addAlert(m, false)))
    .catch(() => {})
    .finally(() => connect());
