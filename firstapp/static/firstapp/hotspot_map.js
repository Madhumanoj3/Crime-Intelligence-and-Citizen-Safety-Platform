/* Crime hotspot map: Leaflet + OpenStreetMap tiles, data from /api/hotspots/ (DBSCAN clusters). */
(function () {
    var el = document.getElementById('hotspotMap');
    if (!el || typeof L === 'undefined') {
        if (el) el.innerHTML = '<div class="map-placeholder" style="height:100%;">Map library could not be loaded. Check your internet connection.</div>';
        return;
    }

    var RISK_COLORS = { High: '#e74c3c', Medium: '#f39c12', Low: '#27ae60' };
    var TN_CENTER = [11.1, 78.6];

    var map = L.map(el, { scrollWheelZoom: false }).setView(TN_CENTER, 7);
    // OSM rejects tile requests without a Referer (HTTP 403). Django's default
    // Referrer-Policy is "same-origin", so send just our origin for tiles only.
    var osmTiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        referrerPolicy: 'strict-origin-when-cross-origin',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // If OSM tiles fail to load (network error / outage), switch once to CARTO's free OSM-based basemap.
    var tileErrors = 0;
    osmTiles.on('tileerror', function () {
        if (++tileErrors !== 4) return;
        map.removeLayer(osmTiles);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            maxZoom: 20,
            subdomains: 'abcd',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
                '&copy; <a href="https://carto.com/attributions">CARTO</a>'
        }).addTo(map);
    });
    map.on('focus', function () { map.scrollWheelZoom.enable(); });
    map.on('blur', function () { map.scrollWheelZoom.disable(); });

    var hotspotLayer = L.layerGroup().addTo(map);
    var pointLayer = L.layerGroup().addTo(map);

    var typeSelect = document.getElementById('hotspotType');
    var yearSelect = document.getElementById('hotspotYear');
    var citySelect = document.getElementById('hotspotCity');
    var pointsToggle = document.getElementById('hotspotShowPoints');
    var summary = document.getElementById('hotspotSummary');
    var tableBody = document.getElementById('hotspotTableBody');

    var userLat = parseFloat(el.dataset.userLat);
    var userLon = parseFloat(el.dataset.userLon);
    var hasUserLocation = !isNaN(userLat) && !isNaN(userLon);
    if (hasUserLocation) {
        L.marker([userLat, userLon]).addTo(map)
            .bindPopup('<strong>Your area</strong>' + (el.dataset.userArea ? '<br>' + escapeHtml(el.dataset.userArea) : ''));
    }
    var firstLoad = true;

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function fillOptions(select, values) {
        if (select.options.length > 1) return;
        values.forEach(function (v) { select.add(new Option(v, v)); });
    }

    function goToArea() {
        var v = citySelect.value;
        if (v) {
            var p = v.split(',').map(Number);
            map.setView([p[0], p[1]], p[2]);
        } else if (hasUserLocation) {
            map.setView([userLat, userLon], 13);
        } else {
            map.setView(TN_CENTER, 7);
        }
    }

    // Legend text shows the complaint counts behind each colour, e.g. "High (6+ complaints)".
    function updateLegend(levels) {
        levels.forEach(function (lvl, i) {
            var span = document.getElementById('legend' + lvl.level);
            if (!span) return;
            var upper = i > 0 ? levels[i - 1].min - 1 : null;
            var range = upper === null ? lvl.min + '+' : (upper === lvl.min ? lvl.min : lvl.min + '–' + upper);
            span.textContent = lvl.level + ' (' + range + ' complaint' + (range === '1' ? '' : 's') + ')';
        });
    }

    function render(data) {
        hotspotLayer.clearLayers();
        pointLayer.clearLayers();
        fillOptions(typeSelect, data.crime_types);
        fillOptions(yearSelect, data.years);

        data.points.forEach(function (p) {
            L.circleMarker([p.lat, p.lon], {
                radius: 3, weight: 0, fillColor: '#34495e', fillOpacity: 0.55
            }).bindPopup(
                '<strong>' + escapeHtml(p.type) + '</strong><br>' + escapeHtml(p.location) +
                '<br>Date: ' + escapeHtml(p.date) + '<br>Status: ' + escapeHtml(p.status) +
                '<br>Hotspot #' + p.cluster
            ).addTo(pointLayer);
        });

        data.clusters.forEach(function (c) {
            var color = RISK_COLORS[c.risk];
            var breakdown = Object.keys(c.crime_breakdown).map(function (k) {
                return escapeHtml(k) + ': ' + c.crime_breakdown[k];
            }).join('<br>');
            var popup = '<strong>Hotspot #' + c.id + ' — ' + escapeHtml(c.area) + '</strong>' +
                '<br>Risk: <strong style="color:' + color + '">' + c.risk + '</strong>' +
                '<br>Complaints: ' + c.count + '<br>Latest: ' + escapeHtml(c.latest) +
                '<hr style="margin:4px 0">' + breakdown;
            L.circle([c.lat, c.lon], {
                radius: c.radius_m, color: color, weight: 2, fillColor: color, fillOpacity: 0.25
            }).bindPopup(popup).addTo(hotspotLayer);
            L.circleMarker([c.lat, c.lon], {
                radius: Math.min(6 + Math.sqrt(c.count) * 1.5, 22),
                color: '#fff', weight: 2, fillColor: color, fillOpacity: 0.9
            }).bindPopup(popup).bindTooltip(escapeHtml(c.area) + ' (' + c.count + ')').addTo(hotspotLayer);
        });

        if (!pointsToggle.checked) map.removeLayer(pointLayer);

        var high = data.clusters.filter(function (c) { return c.risk === 'High'; }).length;
        updateLegend(data.risk_levels);
        summary.className = 'info-box info';
        if (!data.total_incidents) {
            summary.innerHTML = 'ℹ️ No registered complaints with a location' +
                (data.filters.crime_type || data.filters.year ? ' for this filter' : ' yet') +
                '. Hotspots appear here as complaints are filed.';
        } else {
            summary.innerHTML = 'ℹ️ <strong>' + data.total_incidents + ' complaints</strong> grouped into <strong>' +
                data.clusters.length + ' areas</strong> (' + high + ' high crime). Colour is based on the number of ' +
                'complaints in each area; ' + escapeHtml(data.algorithm) + '. <em>Source: ' + escapeHtml(data.source) + '.</em>';
        }

        if (tableBody) {
            tableBody.innerHTML = data.clusters.length ? data.clusters.map(function (c) {
                var badge = { High: 'badge-danger', Medium: 'badge-warning', Low: 'badge-success' }[c.risk];
                return '<tr data-lat="' + c.lat + '" data-lon="' + c.lon + '" style="cursor:pointer">' +
                    '<td>#' + c.id + '</td><td>' + escapeHtml(c.area) + '</td><td>' + c.count + '</td>' +
                    '<td>' + escapeHtml(c.primary_crime) + '</td><td>' + escapeHtml(c.latest) + '</td>' +
                    '<td><span class="badge ' + badge + '">' + c.risk + '</span></td></tr>';
            }).join('') : '<tr><td colspan="6">No complaints with a location for this filter.</td></tr>';
        }

        if (firstLoad) {
            firstLoad = false;
            goToArea();
        }
    }

    function load() {
        var params = new URLSearchParams();
        if (typeSelect.value) params.set('crime_type', typeSelect.value);
        if (yearSelect.value) params.set('year', yearSelect.value);
        summary.textContent = 'Loading hotspot analysis…';
        fetch(el.dataset.api + '?' + params.toString())
            .then(function (r) {
                return r.json().then(function (body) {
                    if (!r.ok) throw new Error(body.error || ('HTTP ' + r.status));
                    return body;
                });
            })
            .then(render)
            .catch(function (err) {
                summary.className = 'info-box warning';
                summary.textContent = '⚠️ Could not load hotspot data: ' + err.message;
            });
    }

    typeSelect.addEventListener('change', load);
    yearSelect.addEventListener('change', load);
    citySelect.addEventListener('change', goToArea);
    pointsToggle.addEventListener('change', function () {
        if (pointsToggle.checked) pointLayer.addTo(map); else map.removeLayer(pointLayer);
    });
    if (tableBody) {
        tableBody.addEventListener('click', function (e) {
            var row = e.target.closest('tr[data-lat]');
            if (!row) return;
            map.setView([+row.dataset.lat, +row.dataset.lon], 15);
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    load();
})();
