/* ── Utilities ────────────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);
const delay = ms => new Promise(r => setTimeout(r, ms));

function esc(s) {
    return String(s)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ── Pipeline animation ──────────────────────────────────────────────────── */
function resetPipeline() {
    for (let i = 1; i <= 5; i++) {
        const s = $(`step-${i}`);
        s.classList.remove("active", "done-safe", "done-flagged");
        $(`val-${i}`).textContent = "—";
        if (i <= 5) $(`val-${i}`).className = i === 5 ? "verdict-value" : "step-value";
    }
    for (let i = 1; i <= 4; i++) $(`conn-${i}`).classList.remove("lit");
}

async function activateStep(n) {
    $(`step-${n}`).classList.add("active");
    if (n > 1) $(`conn-${n - 1}`).classList.add("lit");
    await delay(480);
}

function completeStep(n, flagged) {
    const s = $(`step-${n}`);
    s.classList.remove("active");
    s.classList.add(flagged ? "done-flagged" : "done-safe");
}

async function runPipeline(raw, a) {
    resetPipeline();

    // 01 – Input
    await activateStep(1);
    $("val-1").textContent = raw;
    completeStep(1, false);

    // 02 – Preprocessing
    await activateStep(2);
    $("val-2").textContent = a.preprocessed;
    completeStep(2, false);

    // 03 – Pattern matching
    await activateStep(3);
    $("val-3").textContent = a.matched_patterns.length
        ? `${a.matched_patterns.length} match(es): ${a.categories.join(", ")}`
        : "No threat patterns detected";
    completeStep(3, a.matched_patterns.length > 0);

    // 04 – Risk evaluation
    await activateStep(4);
    $("val-4").textContent = `Score: ${a.risk_score}  ·  ${a.risk_level.toUpperCase()}`;
    completeStep(4, a.is_flagged);

    // 05 – Output
    await activateStep(5);
    const v = $("val-5");
    if (a.is_flagged) {
        v.textContent = "⚠ FLAGGED";
        v.className = `verdict-value verdict-${a.risk_level}`;
    } else {
        v.textContent = "✓ SAFE";
        v.className = "verdict-value verdict-safe";
    }
    completeStep(5, a.is_flagged);
}

/* ── Render a message card ────────────────────────────────────────────────── */
function addMessage(data) {
    const box = $("messages");
    const empty = box.querySelector(".empty-state");
    if (empty) empty.remove();

    const { sender, content, timestamp, analysis: a } = data;

    const cats = a.categories.map(c => `<span class="tag">${esc(c)}</span>`).join("");

    const card = document.createElement("div");
    card.className = `message-card risk-${a.risk_level}`;
    card.innerHTML = `
        <div class="msg-meta">
            <span class="msg-sender">${esc(sender)}</span>
            <span class="msg-time">${esc(timestamp)}</span>
        </div>
        <div class="msg-content">${esc(content)}</div>
        <div class="msg-footer">
            <span class="risk-badge badge-${a.risk_level}">${a.risk_level.toUpperCase()}</span>
            ${cats}
        </div>`;

    box.appendChild(card);
    box.scrollTop = box.scrollHeight;
}

/* ── Send message ─────────────────────────────────────────────────────────── */
async function sendMessage() {
    const sender  = $("sender").value.trim() || "Anonymous";
    const content = $("content").value.trim();
    if (!content) return;

    const btn = $("send-btn");
    btn.disabled = true;
    $("content").value = "";

    try {
        const res  = await fetch("/send", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ sender, content }),
        });
        const data = await res.json();
        addMessage(data);
        await runPipeline(content, data.analysis);
    } catch (e) {
        console.error("Send failed:", e);
    } finally {
        btn.disabled = false;
    }
}

/* ── Keyboard shortcut ────────────────────────────────────────────────────── */
$("content").addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});

/* ── Clear session ────────────────────────────────────────────────────────── */
async function clearSession() {
    await fetch("/clear", { method: "POST" }).catch(() => {});
    const box = $("messages");
    box.innerHTML = `<div class="empty-state"><span>💬</span>Session cleared.<br>Send a message to begin monitoring.</div>`;
    resetPipeline();
}

