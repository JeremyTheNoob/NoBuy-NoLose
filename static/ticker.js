/**
 * 首页动态 K 线走势图
 */
(function() {
    var canvas = document.getElementById("tickerCanvas");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");

    var W, H, bars = [], maxBars, barWidth = 3, gap = 1, speed = 1.2;
    var price = 100 + Math.random() * 40;
    var volatility = 0.02;
    var trend = 0;

    function resize() {
        var rect = canvas.parentElement.getBoundingClientRect();
        var dpr = window.devicePixelRatio || 1;
        W = rect.width;
        H = rect.height;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + "px";
        canvas.style.height = H + "px";
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        maxBars = Math.floor(W / (barWidth + gap));
        // Trim bars if needed
        while (bars.length > maxBars) bars.shift();
    }

    function candle() {
        trend += (Math.random() - 0.48) * 0.15;
        trend = Math.max(-1, Math.min(1, trend));
        var change = (Math.random() - 0.5) * volatility + trend * volatility * 0.3;
        price = price * (1 + change);
        price = Math.max(20, Math.min(300, price));

        var open = price;
        var body = (Math.random() - 0.5) * price * volatility * 2;
        var close = open + body;
        var high = Math.max(open, close) + Math.random() * price * volatility * 1.5;
        var low = Math.min(open, close) - Math.random() * price * volatility * 1.5;

        bars.push({ open: open, high: high, low: low, close: close });
        if (bars.length > maxBars + 10) bars.shift();
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);

        if (bars.length < 2) return;

        // Find min/max for scaling
        var min = Infinity, max = -Infinity, lastClose = 0;
        for (var i = 0; i < bars.length; i++) {
            if (bars[i].low < min) min = bars[i].low;
            if (bars[i].high > max) max = bars[i].high;
            lastClose = bars[i].close;
        }
        var range = max - min || 1;
        var pad = range * 0.15;
        min -= pad; max += pad; range = max - min;

        // Draw grid lines
        ctx.strokeStyle = "rgba(0,0,0,0.04)";
        ctx.lineWidth = 1;
        for (var g = 0; g < 5; g++) {
            var gy = (H * 0.1) + (H * 0.8) * g / 4;
            ctx.beginPath();
            ctx.moveTo(0, gy); ctx.lineTo(W, gy);
            ctx.stroke();
        }

        // Draw candles
        var x = W - (bars.length * (barWidth + gap));
        for (var i = 0; i < bars.length; i++) {
            var b = bars[i];
            var cx = x + i * (barWidth + gap);

            var oy = H * 0.1 + (H * 0.8) * (1 - (b.open - min) / range);
            var cy = H * 0.1 + (H * 0.8) * (1 - (b.close - min) / range);
            var hy = H * 0.1 + (H * 0.8) * (1 - (b.high - min) / range);
            var ly = H * 0.1 + (H * 0.8) * (1 - (b.low - min) / range);

            // Wick
            ctx.strokeStyle = b.close >= b.open ? "#27ae60" : "#c0392b";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(cx + barWidth/2, hy);
            ctx.lineTo(cx + barWidth/2, ly);
            ctx.stroke();

            // Body
            var bodyTop = Math.min(oy, cy);
            var bodyH = Math.max(Math.abs(cy - oy), 1);
            ctx.fillStyle = b.close >= b.open ? "#27ae60" : "#c0392b";
            ctx.fillRect(cx, bodyTop, barWidth, bodyH);
        }

        // Price line (white with subtle glow)
        if (bars.length > 0) {
            var lastY = H * 0.1 + (H * 0.8) * (1 - (lastClose - min) / range);
            ctx.strokeStyle = "rgba(0,102,179,0.18)";
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(0, lastY); ctx.lineTo(W, lastY);
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }

    function tick() {
        candle();
        draw();
    }

    // Throttled resize
    var resizeTimer;
    window.addEventListener("resize", function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() { resize(); draw(); }, 150);
    });

    resize();
    // Pre-fill some bars
    for (var i = 0; i < maxBars * 0.8; i++) candle();
    draw();
    setInterval(tick, 1000 / 30); // 30fps
})();
