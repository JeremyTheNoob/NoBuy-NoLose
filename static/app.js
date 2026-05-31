var TIMEOUT = 60000, abortCtrl = null;

document.getElementById("analyzeBtn").addEventListener("click", run);
document.getElementById("abortBtn").addEventListener("click", abort);
document.getElementById("symbolInput").addEventListener("keydown", function(e) {
    if (e.key === "Enter") run();
});

function abort() {
    if (abortCtrl) abortCtrl.abort();
    abortCtrl = null;
    hide("loading");
    document.getElementById("analyzeBtn").disabled = false;
}

async function run() {
    var symbol = document.getElementById("symbolInput").value.trim();
    if (!/^\d{6}$/.test(symbol)) return showError("请输入 6 位数字 A 股代码");

    var btn = document.getElementById("analyzeBtn");
    btn.disabled = true;
    hide("error"); hide("result"); hide("emptyState");
    show("loading");

    abortCtrl = new AbortController();
    var tid = setTimeout(function() { abortCtrl.abort(); }, TIMEOUT);

    try {
        var resp = await fetch("/analyze", { method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: symbol }),
            signal: abortCtrl.signal });
        clearTimeout(tid);

        if (resp.status === 402) {
            var err = await resp.json();
            showPaywall(err.detail || "试用已用完");
            hide("loading"); btn.disabled = false;
            return;
        }

        if (!resp.ok) throw new Error(((await resp.json()).detail) || "请求失败");
        render(await resp.json());
    } catch (e) {
        if (e.name !== "AbortError") showError(e.message);
        else showError("请求超时，请检查网络后重试");
    } finally {
        clearTimeout(tid); abortCtrl = null;
        hide("loading"); btn.disabled = false;
    }
}

async function checkLicenseStatus() {
    try {
        var resp = await fetch("/license");
        var data = await resp.json();
        if (data.reason === "trial") {
            showTrialBadge(data.remaining);
        }
    } catch(e) {}
}

function showTrialBadge(remaining) {
    var badge = document.getElementById("trialBadge");
    if (!badge) {
        badge = document.createElement("div");
        badge.id = "trialBadge";
        badge.style.cssText = "text-align:center;margin-bottom:12px;font-size:12px;color:var(--orange);";
        document.querySelector(".search-bar").after(badge);
    }
    badge.textContent = "免费试用剩余 " + remaining + " 次 · 888 元解锁无限分析";
    badge.style.cursor = "pointer";
    badge.onclick = function() { showPaywall(""); };
}

function showPaywall(msg) {
    hide("result"); hide("loading"); show("emptyState");
    document.getElementById("emptyState").innerHTML =
        '<div class="paywall">' +
        '<div class="paywall-icon">&#9733;</div>' +
        '<h2>' + (msg || "免费试用已用完") + '</h2>' +
        '<p style="margin-top:8px;color:var(--text2)">888 元解锁终身无限分析 · 绑定本机</p>' +
        '<div class="paywall-features">' +
        '<span>10条AI深度理由</span><span>四维度全量数据</span><span>每日自动更新</span>' +
        '</div>' +
        '<p style="margin-top:16px;font-size:12px;color:var(--muted)">获取方式：联系卖方获取 License Key</p>' +
        '<p style="font-size:12px;color:var(--muted)">将 Key 文件放入 data/license.key 后重启</p>' +
        '</div>';
}

// ---- RENDER ----

function render(d) {
    var h = d.summary, reasons = d.reasons, raw = d.data || {};

    // Quote header
    document.getElementById("qhName").textContent = d.stock_name;
    document.getElementById("qhCode").textContent = d.symbol;
    document.getElementById("qhIndustry").textContent = raw.industry ? raw.industry : "--";
    document.getElementById("qhSource").textContent = "数据 " + h.provider + " · AI " + h.ai_provider;

    document.getElementById("qkPrice").textContent = raw.price ? raw.price.toFixed(2) : "--";
    document.getElementById("qkPE").textContent = raw.pe ? raw.pe.toFixed(1) : "--";
    document.getElementById("qkPB").textContent = raw.pb ? raw.pb.toFixed(2) : "--";
    document.getElementById("qkAI").textContent = h.ai_provider || "未启用";

    // Risk overview
    var total = h.high + h.medium + h.low || 1;
    document.getElementById("riskOverview").innerHTML =
        '<span class="risk-title">风险总览</span>' +
        '<div class="risk-bar-wrap">' +
          '<div class="rb high" style="width:' + (h.high/total*100) + '%"></div>' +
          '<div class="rb medium" style="width:' + (h.medium/total*100) + '%"></div>' +
          '<div class="rb low" style="width:' + (h.low/total*100) + '%"></div>' +
        '</div>' +
        '<div class="risk-legend">' +
          '<span class="rl"><span class="rl-dot c-high"></span> 高风险 ' + h.high + '</span>' +
          '<span class="rl"><span class="rl-dot c-medium"></span> 中等 ' + h.medium + '</span>' +
          '<span class="rl"><span class="rl-dot c-low"></span> 低风险 ' + h.low + '</span>' +
        '</div>';

    // Group reasons by dimension
    var groups = {};
    for (var i = 0; i < reasons.length; i++) {
        var dim = reasons[i].dimension || "综合";
        if (!groups[dim]) groups[dim] = [];
        groups[dim].push(reasons[i]);
    }

    // Order: 估值 → 财务质量 → 技术面 → 风险事件 → 综合
    var order = ["估值", "财务质量", "技术面", "风险事件", "综合", "数据提示"];
    var html = "";
    var globalIdx = 0;
    for (var o = 0; o < order.length; o++) {
        var key = order[o];
        if (!groups[key]) continue;
        var items = groups[key];
        html += '<div class="dim-group">';
        html += '<div class="dim-group-header"><span>' + key + '</span><span class="dg-count">' + items.length + ' 条</span></div>';
        for (var j = 0; j < items.length; j++) {
            globalIdx++;
            var r = items[j];
            html += '<div class="reason-row sev-' + r.severity + '">';
            html += '<div class="r-num">' + globalIdx + '</div>';
            html += '<div class="r-body">';
            html += '<div class="r-top"><span class="sev-tag ' + r.severity + '">' + sevLabel(r.severity) + '</span></div>';
            html += '<div class="r-title">' + r.conclusion + '</div>';
            html += '<div class="r-detail">' + r.data_support + '</div>';
            html += '<div class="r-impact">' + r.impact + '</div>';
            html += '</div></div>';
        }
        html += '</div>';
        delete groups[key];
    }
    // Any remaining dimensions
    for (var k in groups) {
        if (!groups.hasOwnProperty(k)) continue;
        var items2 = groups[k];
        html += '<div class="dim-group"><div class="dim-group-header"><span>' + k + '</span><span class="dg-count">' + items2.length + ' 条</span></div>';
        for (var j2 = 0; j2 < items2.length; j2++) {
            globalIdx++;
            var r2 = items2[j2];
            html += '<div class="reason-row sev-' + r2.severity + '">';
            html += '<div class="r-num">' + globalIdx + '</div><div class="r-body">';
            html += '<div class="r-top"><span class="sev-tag ' + r2.severity + '">' + sevLabel(r2.severity) + '</span></div>';
            html += '<div class="r-title">' + r2.conclusion + '</div>';
            html += '<div class="r-detail">' + r2.data_support + '</div>';
            html += '<div class="r-impact">' + r2.impact + '</div>';
            html += '</div></div>';
        }
        html += '</div>';
    }
    document.getElementById("dimensionGroups").innerHTML = html;

    // Sidebar
    document.getElementById("sideNumbers").innerHTML =
        '<h3>关键数字</h3>' +
        '<div class="side-stat"><span class="ss-label">高风险</span><span class="ss-value" style="color:var(--red)">' + h.high + ' 条</span></div>' +
        '<div class="side-stat"><span class="ss-label">中等风险</span><span class="ss-value" style="color:var(--orange)">' + h.medium + ' 条</span></div>' +
        '<div class="side-stat"><span class="ss-label">低风险</span><span class="ss-value" style="color:var(--green)">' + h.low + ' 条</span></div>';

    document.getElementById("sideMeta").innerHTML =
        "耗时 " + h.elapsed_seconds + "s &middot; 数据源 " + h.provider + "<br>AI: " + h.ai_provider;

    hide("error");
    show("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
    setTimeout(function() {
        document.getElementById("result").scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
}

// ---- helpers ----

function sevLabel(s) {
    var map = { high: "高风险", medium: "中等风险", low: "低风险" };
    return map[s] || s;
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }
function showError(msg) {
    hide("result"); show("emptyState");
    var e = document.getElementById("error");
    e.textContent = msg; show("error");
}

// 页面初始化：检查 License 状态
checkLicenseStatus();
