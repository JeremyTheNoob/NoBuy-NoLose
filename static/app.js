const SEVERITY_LABELS = { high: "高风险", medium: "中等风险", low: "低风险" };
const REQUEST_TIMEOUT_MS = 60000;

let abortController = null;

document.getElementById("analyzeBtn").addEventListener("click", runAnalysis);
document.getElementById("abortBtn").addEventListener("click", abortAnalysis);
document.getElementById("symbolInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runAnalysis();
});

function abortAnalysis() {
    if (abortController) {
        abortController.abort();
        abortController = null;
    }
    hide("loading");
    document.getElementById("analyzeBtn").disabled = false;
    showError("分析已取消");
}

async function runAnalysis() {
    const symbol = document.getElementById("symbolInput").value.trim();
    if (!/^\d{6}$/.test(symbol)) {
        showError("请输入6位数字的A股代码");
        return;
    }

    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;

    hide("error");
    hide("result");
    document.getElementById("loadingText").textContent = "正在获取数据并分析中...";
    show("loading");

    abortController = new AbortController();
    const timeoutId = setTimeout(() => abortController.abort(), REQUEST_TIMEOUT_MS);

    try {
        const resp = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol }),
            signal: abortController.signal,
        });

        clearTimeout(timeoutId);

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "分析失败");
        }

        const data = await resp.json();
        renderResult(data);
    } catch (e) {
        if (e.name === "AbortError") {
            showError(e.message || "请求超时，请检查网络后重试");
        } else {
            showError(e.message);
        }
    } finally {
        clearTimeout(timeoutId);
        abortController = null;
        hide("loading");
        btn.disabled = false;
    }
}

function renderResult(data) {
    document.getElementById("stockHeader").innerHTML = `
        <h2>${data.stock_name} (${data.symbol})</h2>
        <p class="meta">数据源: ${data.summary.provider} | AI: ${data.summary.ai_provider} | 耗时: ${data.summary.elapsed_seconds}s</p>
    `;

    const reasonsDiv = document.getElementById("reasons");
    reasonsDiv.innerHTML = data.reasons.map((r, i) => `
        <div class="reason-card severity-${r.severity}">
            <div class="card-header">
                <span class="dimension-tag">${r.dimension}</span>
                <span class="severity-tag ${r.severity}">${SEVERITY_LABELS[r.severity] || r.severity}</span>
            </div>
            <div class="conclusion">${i + 1}. ${r.conclusion}</div>
            <div class="data-support">${r.data_support}</div>
            <div class="impact">${r.impact}</div>
        </div>
    `).join("");

    document.getElementById("summary").innerHTML = `
        <div class="stats">
            <div class="stat">
                <div class="num high">${data.summary.high}</div>
                <div class="label">高风险</div>
            </div>
            <div class="stat">
                <div class="num medium">${data.summary.medium}</div>
                <div class="label">中等风险</div>
            </div>
            <div class="stat">
                <div class="num low">${data.summary.low}</div>
                <div class="label">低风险</div>
            </div>
        </div>
        <div class="meta">
            ${data.summary.elapsed_seconds}s | ${data.summary.provider} | ${data.summary.ai_provider}
        </div>
    `;

    hide("error");
    show("result");
    window.scrollTo({ top: document.getElementById("result").offsetTop - 20, behavior: "smooth" });
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }

function showError(msg) {
    hide("result");
    const el = document.getElementById("error");
    el.textContent = msg;
    show("error");
}
