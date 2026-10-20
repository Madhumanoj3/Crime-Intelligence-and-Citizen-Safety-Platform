/* =============================================================================
   CISP UI SCRIPT (ui.js)
   Interactive UI enhancements: count-up stats, hero typing, sidebar toggle,
   form focus, notification badges, table row stagger.
   ============================================================================= */
(function () {
    'use strict';
    if (window.__cispUI) return;
    window.__cispUI = true;

    var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

    /* ---------- GLOBAL SIDEBAR TOGGLE ---------- */
    window.toggleSidebar = function () {
        var sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('active');
        }
    };

    /* ---------- COUNT-UP ANIMATION FOR STATS ---------- */
    function countUp(el) {
        var target = parseInt(el.dataset.count || el.textContent.replace(/[^0-9]/g, ''), 10) || 0;
        if (!target) return;
        el.dataset.count = target;
        el.textContent = '0';
        var duration = Math.min(1800, 600 + target * 2);
        var start = null;
        function step(ts) {
            if (!start) start = ts;
            var progress = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target);
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        if (reduced) { el.textContent = target; return; }
        requestAnimationFrame(step);
    }

    function initCountUp() {
        var nums = document.querySelectorAll('.stat-number, .hero-stat-number');
        if (!nums.length) return;
        if (!('IntersectionObserver' in window)) {
            nums.forEach(countUp);
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (!e.isIntersecting) return;
                countUp(e.target);
                io.unobserve(e.target);
            });
        }, { threshold: 0.2 });
        nums.forEach(function (el) { io.observe(el); });
    }

    /* ---------- HERO HEADLINE TYPING EFFECT ---------- */
    function initTyping() {
        var el = document.querySelector('.typing-text');
        if (!el || reduced) return;
        var full = el.dataset.text || el.textContent;
        el.dataset.text = full;
        el.textContent = '';
        var i = 0;
        var delay = parseInt(el.dataset.delay || 600, 10);
        setTimeout(function type() {
            if (i <= full.length) {
                el.textContent = full.slice(0, i);
                i++;
                setTimeout(type, 45 + Math.random() * 25);
            }
        }, delay);
    }

    /* ---------- CITY SILHOUETTE CANVAS (HERO ONLY) ---------- */
    function buildCityCanvas(hero) {
        var canvas = document.createElement('canvas');
        canvas.className = 'city-canvas-layer';
        canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;';
        hero.insertBefore(canvas, hero.firstChild);

        function resize() {
            canvas.width = hero.offsetWidth || window.innerWidth;
            canvas.height = hero.offsetHeight || 500;
        }

        function draw() {
            var ctx = canvas.getContext('2d');
            var W = canvas.width, H = canvas.height;
            ctx.clearRect(0, 0, W, H);

            var buildings = [
                {x:0,w:60,h:.25},{x:55,w:45,h:.35},{x:95,w:35,h:.55},{x:125,w:55,h:.42},
                {x:175,w:40,h:.62},{x:210,w:30,h:.48},{x:235,w:60,h:.38},{x:290,w:45,h:.58},
                {x:330,w:35,h:.72},{x:360,w:50,h:.5},{x:405,w:40,h:.65},{x:440,w:70,h:.45},
                {x:505,w:35,h:.38},{x:535,w:55,h:.6},{x:585,w:45,h:.52},{x:625,w:30,h:.4},
                {x:650,w:65,h:.35},{x:710,w:40,h:.55},{x:745,w:35,h:.68},{x:775,w:55,h:.45},
                {x:825,w:45,h:.38},{x:865,w:60,h:.3},{x:920,w:35,h:.5},{x:950,w:50,h:.42},
                {x:995,w:45,h:.6},{x:1035,w:65,h:.35},{x:1095,w:40,h:.48},{x:1130,w:55,h:.55},
                {x:1180,w:35,h:.38},{x:1210,w:60,h:.45}
            ];
            var sx = W / 1280;

            // Silhouette
            ctx.fillStyle = 'rgba(8, 25, 55, 0.75)';
            ctx.beginPath();
            ctx.moveTo(0, H);
            buildings.forEach(function (b) {
                var bx = b.x * sx, bw = b.w * sx, by = H - H * b.h;
                ctx.lineTo(bx, H);
                ctx.lineTo(bx, by);
                ctx.lineTo(bx + bw, by);
                ctx.lineTo(bx + bw, H);
            });
            ctx.lineTo(W, H);
            ctx.closePath();
            ctx.fill();

            // Window lights
            var seed = 42;
            function rng() { seed = (seed * 1664525 + 1013904223) & 0xffffffff; return (seed >>> 0) / 0xffffffff; }
            buildings.forEach(function (b) {
                var bx = b.x * sx + 4, bw = b.w * sx - 8, bh = H * b.h - 8, by = H - bh;
                var cols = Math.max(1, Math.floor(bw / 12)), rows = Math.max(1, Math.floor(bh / 16));
                for (var r = 0; r < rows; r++) {
                    for (var c = 0; c < cols; c++) {
                        if (rng() > 0.45) {
                            ctx.fillStyle = 'rgba(255, 220, 100, 0.6)';
                            ctx.fillRect(bx + c * (bw / cols) + 2, by + r * (bh / rows) + 3, 4, 5);
                        }
                    }
                }
            });

            // Ground gradient
            var gnd = ctx.createLinearGradient(0, H * 0.72, 0, H);
            gnd.addColorStop(0, 'rgba(10, 30, 60, 0)');
            gnd.addColorStop(1, 'rgba(10, 30, 60, 0.9)');
            ctx.fillStyle = gnd;
            ctx.fillRect(0, H * 0.72, W, H * 0.28);

            // Police patrol light beams
            var now = Date.now() / 1000;
            [[0.28, 'rgba(77, 168, 232, 0.08)'], [0.72, 'rgba(232, 85, 85, 0.07)']].forEach(function (beam, si) {
                var angle = now * (si === 0 ? 0.35 : -0.3) + si * Math.PI;
                var gx = W * beam[0], gy = H * 0.9;
                ctx.save();
                ctx.fillStyle = beam[1];
                ctx.beginPath();
                ctx.moveTo(gx, gy);
                ctx.arc(gx, gy, H * 1.5, angle - 0.1, angle + 0.1);
                ctx.closePath();
                ctx.fill();
                ctx.restore();
            });
        }

        resize();
        if (reduced) { draw(); return; }
        function animate() {
            draw();
            requestAnimationFrame(animate);
        }
        animate();
        var t;
        window.addEventListener('resize', function () {
            clearTimeout(t);
            t = setTimeout(resize, 150);
        });
    }

    /* ---------- NOTIFICATION BADGE ---------- */
    function initNotifBell() {
        document.querySelectorAll('.header-icon').forEach(function (el) {
            if (el.textContent.trim() === '🔔' && !el.closest('.notif-bell-wrapper')) {
                var w = document.createElement('span');
                w.className = 'notif-bell-wrapper';
                w.style.cssText = 'position:relative;display:inline-block;cursor:pointer;';
                el.parentNode.insertBefore(w, el);
                w.appendChild(el);
                var dot = document.createElement('span');
                dot.className = 'notif-badge';
                dot.style.cssText = 'position:absolute;top:-2px;right:-2px;width:8px;height:8px;background:#e74c3c;border-radius:50%;border:2px solid #fff;';
                w.appendChild(dot);
            }
        });
    }

    /* ---------- FORM FOCUS HIGHLIGHTS ---------- */
    function initFormFocus() {
        document.querySelectorAll('input, select, textarea').forEach(function (input) {
            input.addEventListener('focus', function () {
                var g = input.closest('.form-group');
                if (g) g.classList.add('focused');
            });
            input.addEventListener('blur', function () {
                var g = input.closest('.form-group');
                if (g) g.classList.remove('focused');
            });
        });
    }

    /* ---------- INITIALIZE ---------- */
    function init() {
        initCountUp();
        initTyping();
        initNotifBell();
        initFormFocus();

        var hero = document.querySelector('.hero-cinematic');
        if (hero) buildCityCanvas(hero);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
