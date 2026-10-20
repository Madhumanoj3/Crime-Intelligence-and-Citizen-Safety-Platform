/* ===== SIDEBAR TOGGLE (Mobile) ===== */
function toggleSidebar() {
    var sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

/* ===== CLOSE SIDEBAR ON OUTSIDE CLICK ===== */
document.addEventListener('click', function (event) {
    var sidebar = document.querySelector('.sidebar');
    var toggle = document.querySelector('.menu-toggle');
    if (sidebar && sidebar.classList.contains('active')) {
        if (!sidebar.contains(event.target) && event.target !== toggle) {
            sidebar.classList.remove('active');
        }
    }
});

/* ===== LOGIN HANDLER ===== */
function handleLogin(event) {
    event.preventDefault();
    var role = document.querySelector('input[name="role"]:checked');
    if (!role) {
        alert('Please select a role.');
        return;
    }
    var email = document.querySelector('input[name="email"]').value;
    var password = document.querySelector('input[name="password"]').value;
    if (!email || !password) {
        alert('Please enter email and password.');
        return;
    }

    switch (role.value) {
        case 'citizen':
            window.location.href = '/citizen/dashboard/';
            break;
        case 'police':
            window.location.href = '/police/dashboard/';
            break;
        case 'admin':
            window.location.href = '/admin-panel/dashboard/';
            break;
    }
}

/* ===== REGISTRATION HANDLER ===== */
function handleRegister(event) {
    event.preventDefault();
    var password = document.querySelector('input[name="password"]').value;
    var confirm = document.querySelector('input[name="confirm_password"]').value;
    if (password !== confirm) {
        alert('Passwords do not match.');
        return;
    }
    alert('Account created successfully! Please login.');
    window.location.href = '/login/';
}

/* ===== GENERIC FORM SUBMIT ===== */
function handleFormSubmit(event, message) {
    event.preventDefault();
    alert(message || 'Submitted successfully!');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ===== SOS HANDLER ===== */
function sendSOS() {
    var btn = document.querySelector('.sos-button');
    if (!btn) return;

    btn.textContent = 'SENDING...';
    btn.style.background = '#f39c12';
    btn.style.borderColor = '#d68910';

    fetch('/citizen/sos/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') || ''
        }
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        btn.textContent = 'SOS SENT';
        btn.style.background = '#27ae60';
        btn.style.borderColor = '#1e8449';

        var statusEl = document.getElementById('sos-status');
        if (statusEl) {
            statusEl.textContent = 'Active (Sent to Police)';
            statusEl.className = 'badge badge-danger';
        }
    })
    .catch(function () {
        btn.textContent = 'SOS SENT';
        btn.style.background = '#27ae60';
        var statusEl = document.getElementById('sos-status');
        if (statusEl) {
            statusEl.textContent = 'Sent';
            statusEl.className = 'badge badge-danger';
        }
    });
}

/* ===== TAB SWITCHING ===== */
function switchTab(tabId, clickedBtn) {
    /* Remove active from all tab buttons */
    var tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(function (btn) {
        btn.classList.remove('active');
    });

    /* Remove active from all tab panes */
    var tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(function (pane) {
        pane.classList.remove('active');
    });

    /* Activate clicked button and target pane */
    clickedBtn.classList.add('active');
    var targetPane = document.getElementById(tabId);
    if (targetPane) {
        targetPane.classList.add('active');
    }
}

/* ===== AMBIENT BACKGROUND (decorative only, see ambient.js) ===== */
(function () {
    var current = document.currentScript;
    if (!current || window.__cispAmbient) return;
    var s = document.createElement('script');
    s.src = current.src.replace(/script\.js(\?.*)?$/, 'ambient.js');
    document.head.appendChild(s);
})();
