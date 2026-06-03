var TIMEOUT = 60000, abortCtrl = null, configured = false;

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

// ---- setup ----

async function checkConfig() {
    try {
        var resp = await fetch("/api/config");
        if (!resp.ok) return;
        var data = await resp.json();
        configured = data.configured;
        if (configured) {
            hide("setupPage");
            show("emptyState");
            document.getElementById("settingsBtn").classList.remove("hidden");
        } else {
            prefillSetupForm(data.config);
            hide("emptyState");
            show("setupPage");
        }
    } catch (e) {
        // server not ready, show normal UI
    }
}

function prefillSetupForm(config) {
    var d = config.data || {}, ai = config.ai || {};

    // Data source: detect which one is configured
    var customApi = d.custom_api || {};
    var hasCustomApi = !!(customApi.api_key);
    var ds = hasCustomApi ? "custom_api" : "tushare";
    document.getElementById("dataSource").value = ds;
    updateDataSourceFields(ds);
    document.getElementById("tsToken").value = (d.tushare || {}).token || "";
    document.getElementById("customApiUrl").value = customApi.url || "";
    document.getElementById("customApiKey").value = customApi.api_key || "";

    var provider = ai.provider || "none";
    document.getElementById("aiProvider").value = provider;
    updateProviderFields(provider);
    if (provider === "none") return;
    var prov = ai[provider] || {};
    if (provider === "ollama") {
        document.getElementById("ollamaHost").value = prov.host || "";
        document.getElementById("aiModel").value = prov.model || "";
    } else {
        document.getElementById("aiApiKey").value = prov.api_key || "";
        document.getElementById("aiModel").value = prov.model || "";
        document.getElementById("aiBaseUrl").value = prov.base_url || "";
    }
}

function updateDataSourceFields(ds) {
    if (ds === "custom_api") {
        document.getElementById("tushareFields").classList.add("hidden");
        document.getElementById("customApiFields").classList.remove("hidden");
    } else {
        document.getElementById("tushareFields").classList.remove("hidden");
        document.getElementById("customApiFields").classList.add("hidden");
    }
}

function updateProviderFields(provider) {
    ["apiKeyField","modelField","baseUrlField","ollamaHostField"].forEach(function(id) {
        document.getElementById(id).classList.add("hidden");
    });
    if (provider === "none") return;
    document.getElementById("modelField").classList.remove("hidden");
    if (provider === "ollama") {
        document.getElementById("ollamaHostField").classList.remove("hidden");
    } else {
        document.getElementById("apiKeyField").classList.remove("hidden");
        document.getElementById("baseUrlField").classList.remove("hidden");
    }
}

async function saveSetup() {
    var btn = document.getElementById("saveConfigBtn");
    var errEl = document.getElementById("setupError");
    btn.disabled = true;
    errEl.classList.add("hidden");

    var ds = document.getElementById("dataSource").value;
    var provider = document.getElementById("aiProvider").value;

    if (ds === "tushare") {
        if (!document.getElementById("tsToken").value.trim()) {
            showSetupError("请输入 Tushare Token"); btn.disabled = false; return;
        }
    } else {
        if (!document.getElementById("customApiKey").value.trim()) {
            showSetupError("请输入 License Key"); btn.disabled = false; return;
        }
    }

    if (provider === "none") { showSetupError("请选择 AI 服务商"); btn.disabled = false; return; }

    var apiKey = document.getElementById("aiApiKey").value || "";
    if (provider !== "ollama" && !apiKey) { showSetupError("请输入 API Key"); btn.disabled = false; return; }

    try {
        var resp = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data_source: ds,
                tushare_token: document.getElementById("tsToken").value || "",
                custom_api_url: document.getElementById("customApiUrl").value || "",
                custom_api_key: document.getElementById("customApiKey").value || "",
                ai_provider: provider,
                api_key: apiKey,
                model: document.getElementById("aiModel").value || "",
                base_url: document.getElementById("aiBaseUrl").value || "",
                host: document.getElementById("ollamaHost").value || ""
            })
        });
        if (!resp.ok) { var e = await resp.json(); throw new Error(e.detail || "保存失败"); }
        location.reload();
    } catch (e) {
        showSetupError(e.message);
    } finally {
        btn.disabled = false;
    }
}

function showSetupError(msg) {
    var el = document.getElementById("setupError");
    el.textContent = msg;
    el.classList.remove("hidden");
}

async function showSetupPage() {
    try {
        var resp = await fetch("/api/config");
        var data = await resp.json();
        prefillSetupForm(data.config);
        hide("emptyState"); hide("result"); hide("error");
        show("setupPage");
    } catch (e) {}
}

// ---- event listeners ----
document.getElementById("dataSource").addEventListener("change", function() {
    updateDataSourceFields(this.value);
});
document.getElementById("saveConfigBtn").addEventListener("click", saveSetup);
document.getElementById("aiProvider").addEventListener("change", function() {
    updateProviderFields(this.value);
});
document.getElementById("settingsBtn").addEventListener("click", function() {
    showSetupPage();
});

// check config on load, then updates
(async function init() {
    await checkConfig();
    if (configured) checkUpdate();
})();

// ---- update check ----
async function checkUpdate() {
    try {
        var resp = await fetch("/api/version");
        var data = await resp.json();
        if (data.has_update) {
            var badge = document.getElementById("updateBadge");
            badge.textContent = "v" + data.latest + " 可用";
            badge.classList.remove("hidden");
            badge.onclick = function() { showUpdateModal(data); };
        }
    } catch (e) {}
}

function showUpdateModal(info) {
    var existing = document.querySelector(".update-modal-overlay");
    if (existing) existing.remove();

    var overlay = document.createElement("div");
    overlay.className = "update-modal-overlay";
    overlay.innerHTML =
        '<div class="update-modal">' +
        '<h3>发现新版本 v' + info.latest + '</h3>' +
        '<p>当前版本: v' + info.current + ' &rarr; v' + info.latest + '</p>' +
        (info.release_notes ? '<div class="update-notes">' + info.release_notes + '</div>' : '') +
        '<div class="update-modal-btns">' +
        '<button class="btn-update-later" onclick="this.closest(\'.update-modal-overlay\').remove()">以后再说</button>' +
        '<button class="btn-update-now" id="btnUpdateNow">立即更新</button>' +
        '</div></div>';
    document.body.appendChild(overlay);

    document.getElementById("btnUpdateNow").addEventListener("click", async function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = "更新中...";
        try {
            var resp = await fetch("/api/update", { method: "POST" });
            var data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || "更新失败");
            overlay.querySelector(".update-modal").innerHTML =
                '<h3>更新完成</h3><p>' + data.message + '</p>' +
                '<div class="update-modal-btns"><button class="btn-update-now" onclick="location.reload()">重启服务</button></div>';
        } catch (e) {
            btn.disabled = false;
            btn.textContent = "立即更新";
            alert("更新失败: " + e.message);
        }
    });
}

