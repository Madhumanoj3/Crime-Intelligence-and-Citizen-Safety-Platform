/* =============================================================================
   CISP AMBIENT BACKGROUND SYSTEM (ambient.js)
   Fixed digital safety & security ambient background layer.
   Purely decorative, runs behind all content (z-index: -1).
   ============================================================================= */
(function () {
    'use strict';
    if (window.__cispAmbient) return;
    window.__cispAmbient = true;

    var doc = document;
    var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

    function hashString(str) {
        var h = 2166136261;
        for (var i = 0; i < str.length; i++) {
            h ^= str.charCodeAt(i);
            h = Math.imul(h, 16777619);
        }
        return h >>> 0;
    }

    function seeded(seed) {
        return function () {
            seed |= 0;
            seed = (seed + 0x6D2B79F5) | 0;
            var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
            t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    var rand = seeded(hashString(location.pathname || '/'));
    function between(a, b) { return a + rand() * (b - a); }
    function sign() { return rand() < 0.5 ? -1 : 1; }
    function shuffle(list) {
        for (var i = list.length - 1; i > 0; i--) {
            var j = Math.floor(rand() * (i + 1));
            var t = list[i]; list[i] = list[j]; list[j] = t;
        }
        return list;
    }

    var SYMBOLS = {
        shield: '<path d="M12 2.5l7.5 2.8v5.9c0 4.7-3.2 8.8-7.5 10.3-4.3-1.5-7.5-5.6-7.5-10.3V5.3L12 2.5z"/><path d="M8.8 12l2.2 2.2 4.3-4.4"/>',
        pin: '<path d="M12 21.5s6.8-6 6.8-11.6a6.8 6.8 0 10-13.6 0C5.2 15.5 12 21.5 12 21.5z"/><circle cx="12" cy="9.9" r="2.4"/>',
        radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5.5"/><circle cx="12" cy="12" r="1.6"/><path d="M12 12l6.4-6.4"/>',
        lock: '<rect x="5" y="10.5" width="14" height="10" rx="2.2"/><path d="M8.2 10.5V7.8a3.8 3.8 0 017.6 0v2.7"/><path d="M12 14.5v2.5"/>',
        alert: '<path d="M12 3.2l9.3 16.6H2.7L12 3.2z"/><path d="M12 9.8v4.4"/><path d="M12 17.1v.1"/>',
        node: '<circle cx="5.5" cy="6.5" r="2"/><circle cx="18.5" cy="7.5" r="2"/><circle cx="12" cy="18" r="2"/><path d="M7.5 6.7l9 .6M6.6 8.2l4.4 8M17.5 9.2l-4.5 7.2"/>'
    };

    /* ---------- PARTICLE NETWORK CANVAS ---------- */
    function Network(canvas, opts) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.o = opts || {};
        this.points = [];
        this.pulses = [];
        this.nextPulse = between(1.5, 3.5);
        this.running = false;
        this.visible = true;
        this.last = 0;
        this.acc = 0;
        this.resize();
    }

    Network.prototype.resize = function () {
        var w = window.innerWidth || doc.documentElement.clientWidth || 1280;
        var h = window.innerHeight || doc.documentElement.clientHeight || 800;
        var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
        this.w = w;
        this.h = h;
        this.canvas.width = Math.round(w * dpr);
        this.canvas.height = Math.round(h * dpr);
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        var target = Math.max(30, Math.min(75, Math.round((w * h) / (this.o.density || 20000))));
        while (this.points.length < target) this.points.push(this.makePoint());
        this.points.length = target;
        for (var i = 0; i < this.points.length; i++) {
            var p = this.points[i];
            if (p.x > w + 20 || p.y > h + 20) { p.x = rand() * w; p.y = rand() * h; }
        }
        if (!this.running) this.draw();
    };

    Network.prototype.makePoint = function () {
        var angle = rand() * Math.PI * 2;
        var speed = between(5, 12);
        var isNode = rand() < 0.15;
        return {
            x: rand() * (this.w || 1280),
            y: rand() * (this.h || 800),
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            r: isNode ? between(2.6, 3.8) : between(1.4, 2.2),
            node: isNode,
            phase: rand() * Math.PI * 2
        };
    };

    Network.prototype.step = function (dt) {
        var w = this.w, h = this.h, m = 30;
        for (var i = 0; i < this.points.length; i++) {
            var p = this.points[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.phase += dt * 1.0;
            if (p.x < -m) p.x = w + m; else if (p.x > w + m) p.x = -m;
            if (p.y < -m) p.y = h + m; else if (p.y > h + m) p.y = -m;
        }

        this.nextPulse -= dt;
        if (this.nextPulse <= 0 && this.pulses.length < 4) {
            this.spawnPulse();
            this.nextPulse = between(1.8, 4.0);
        }
        for (var k = this.pulses.length - 1; k >= 0; k--) {
            this.pulses[k].t += dt / this.pulses[k].dur;
            if (this.pulses[k].t >= 1) this.pulses.splice(k, 1);
        }
    };

    Network.prototype.spawnPulse = function () {
        var pts = this.points, link = this.o.link || 150, L2 = link * link;
        for (var tries = 0; tries < 15; tries++) {
            var a = pts[Math.floor(rand() * pts.length)];
            var b = pts[Math.floor(rand() * pts.length)];
            if (!a || a === b) continue;
            var dx = a.x - b.x, dy = a.y - b.y;
            if (dx * dx + dy * dy < L2 * 0.9) {
                this.pulses.push({ a: a, b: b, t: 0, dur: between(1.4, 2.2) });
                return;
            }
        }
    };

    Network.prototype.draw = function () {
        var ctx = this.ctx, pts = this.points, link = this.o.link || 150, L2 = link * link;
        ctx.clearRect(0, 0, this.w, this.h);

        // Connection Lines (vibrant high-tech blue)
        for (var i = 0; i < pts.length; i++) {
            var a = pts[i];
            for (var j = i + 1; j < pts.length; j++) {
                var b = pts[j];
                var dx = a.x - b.x, dy = a.y - b.y;
                var d2 = dx * dx + dy * dy;
                if (d2 < L2) {
                    var strength = 1 - Math.sqrt(d2) / link;
                    ctx.strokeStyle = 'rgba(46, 134, 193, ' + (0.32 * strength).toFixed(3) + ')';
                    ctx.lineWidth = 1.0;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.stroke();
                }
            }
        }

        // Particle Dots
        ctx.fillStyle = 'rgba(46, 134, 193, 0.72)';
        ctx.beginPath();
        for (var p = 0; p < pts.length; p++) {
            if (pts[p].node) continue;
            ctx.moveTo(pts[p].x + pts[p].r, pts[p].y);
            ctx.arc(pts[p].x, pts[p].y, pts[p].r, 0, Math.PI * 2);
        }
        ctx.fill();

        // Node Glows
        for (var n = 0; n < pts.length; n++) {
            var q = pts[n];
            if (!q.node) continue;
            var glow = 0.5 + 0.5 * Math.sin(q.phase);
            ctx.fillStyle = 'rgba(46, 134, 193, 0.95)';
            ctx.beginPath();
            ctx.arc(q.x, q.y, q.r, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = 'rgba(46, 134, 193, ' + (0.25 + glow * 0.35).toFixed(3) + ')';
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.arc(q.x, q.y, q.r + 3 + glow * 4, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Data Pulses
        for (var k = 0; k < this.pulses.length; k++) {
            var pl = this.pulses[k];
            var t = pl.t < 0.5 ? 2 * pl.t * pl.t : 1 - Math.pow(-2 * pl.t + 2, 2) / 2;
            var x = pl.a.x + (pl.b.x - pl.a.x) * t;
            var y = pl.a.y + (pl.b.y - pl.a.y) * t;
            var fade = Math.sin(pl.t * Math.PI);
            var g = ctx.createRadialGradient(x, y, 0, x, y, 10);
            g.addColorStop(0, 'rgba(46, 134, 193, ' + (0.85 * fade).toFixed(3) + ')');
            g.addColorStop(1, 'rgba(46, 134, 193, 0)');
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, Math.PI * 2);
            ctx.fill();
        }
    };

    Network.prototype.start = function () {
        if (reduced) { this.draw(); return; }
        if (this.running) return;
        this.running = true;
        var self = this;
        var FRAME = 1 / 30;
        function tick(now) {
            if (!self.running) return;
            var dt = self.last ? Math.min((now - self.last) / 1000, 0.1) : FRAME;
            self.last = now;
            self.acc += dt;
            if (self.acc >= FRAME) {
                if (self.visible && !doc.hidden) {
                    self.step(self.acc);
                    self.draw();
                }
                self.acc = 0;
            }
            requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    };

    /* ---------- BUILD FIXED BACKGROUND LAYER ---------- */
    function buildBackground() {
        var isDash = !!doc.querySelector('.dashboard-layout');

        var layer = doc.createElement('div');
        layer.className = 'amb-bg';
        layer.setAttribute('aria-hidden', 'true');
        layer.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;overflow:hidden;background:radial-gradient(ellipse at 50% -10%, rgba(214, 234, 248, 0.75), transparent 65%), linear-gradient(180deg, #f3f7fb 0%, #edf3f9 55%, #e6eff7 100%);';

        // Technical map grid
        var grid = doc.createElement('div');
        grid.className = 'amb-grid';
        grid.style.cssText = 'position:absolute;inset:-240px;pointer-events:none;opacity:0.85;background-image:radial-gradient(circle, rgba(26, 82, 118, 0.12) 1.2px, transparent 1.6px), linear-gradient(rgba(26, 82, 118, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(26, 82, 118, 0.05) 1px, transparent 1px);background-size:240px 240px, 48px 48px, 48px 48px;';
        layer.appendChild(grid);

        // Soft ambient light blobs
        var spots = [[18, 22], [82, 18], [65, 82]];
        var tints = ['rgba(46, 134, 193, 0.22)', 'rgba(133, 193, 233, 0.25)', 'rgba(26, 82, 118, 0.14)'];
        spots.forEach(function (spot, idx) {
            var blob = doc.createElement('div');
            blob.className = 'amb-blob';
            var s = 45;
            blob.style.cssText = 'position:absolute;left:' + spot[0] + '%;top:' + spot[1] + '%;width:' + s + 'vmax;height:' + s + 'vmax;margin-left:-' + (s/2) + 'vmax;margin-top:-' + (s/2) + 'vmax;border-radius:50%;background:radial-gradient(circle at 50% 50%, ' + tints[idx] + ' 0%, transparent 68%);pointer-events:none;';
            layer.appendChild(blob);
        });

        // Floating security symbols (discreet, clean, visible behind glass)
        var kinds = ['shield', 'pin', 'radar', 'lock', 'alert', 'node'];
        var xMin = isDash ? 26 : 6;
        kinds.forEach(function (kind, i) {
            var sym = doc.createElement('div');
            sym.className = 'amb-sym amb-sym-' + kind;
            var s = Math.round(between(32, 48));
            var leftPct = between(xMin, 92).toFixed(1);
            var topPct = (10 + (i / kinds.length) * 75).toFixed(1);
            var color = kind === 'alert' ? '#f39c12' : (i % 2 === 0 ? '#1a5276' : '#2e86c1');
            sym.style.cssText = 'position:absolute;left:' + leftPct + '%;top:' + topPct + '%;width:' + s + 'px;height:' + s + 'px;color:' + color + ';opacity:0.22;pointer-events:none;';
            sym.innerHTML = '<svg viewBox="0 0 24 24" width="' + s + '" height="' + s + '" style="width:100%;height:100%;display:block;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;">' + SYMBOLS[kind] + '</svg>';
            layer.appendChild(sym);
        });

        // Particle Canvas
        var canvas = doc.createElement('canvas');
        canvas.className = 'amb-net';
        canvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;display:block;pointer-events:none;';
        layer.appendChild(canvas);

        doc.body.insertBefore(layer, doc.body.firstChild);

        var net = new Network(canvas, { density: 20000, link: 150 });
        net.start();

        var resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function () { net.resize(); }, 150);
        });
    }

    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', buildBackground);
    else buildBackground();
})();
