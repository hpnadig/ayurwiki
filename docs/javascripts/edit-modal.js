// Ayurwiki — Suggest Edit modal with GitHub OAuth
(function () {
  'use strict';

  var API = 'https://api.ayurwiki.org';
  var RAW_BASE = 'https://raw.githubusercontent.com/hpnadig/ayurwiki/main/docs/';
  var STORAGE_KEY = 'ayurwiki_github';

  // --- Auth state ---

  function getAuth() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null;
    } catch (_) {
      return null;
    }
  }

  function setAuth(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function clearAuth() {
    localStorage.removeItem(STORAGE_KEY);
  }

  // --- Handle OAuth callback from hash ---

  function handleAuthCallback() {
    var hash = window.location.hash;
    if (!hash || hash.indexOf('token=') === -1) return false;

    var params = new URLSearchParams(hash.substring(1));
    var token = params.get('token');
    var error = params.get('auth_error');

    if (error) {
      alert('Login failed: ' + error);
      history.replaceState(null, '', window.location.pathname + window.location.search);
      return false;
    }

    if (token) {
      setAuth({
        token: token,
        login: params.get('login') || '',
        name: params.get('name') || '',
        avatar_url: params.get('avatar_url') || ''
      });
      history.replaceState(null, '', window.location.pathname + window.location.search);
      return true;
    }
    return false;
  }

  // --- Get article path from current URL ---

  function getArticlePath() {
    var path = window.location.pathname.replace(/^\//, '').replace(/\/$/, '');
    if (!path || path === '') path = 'index';
    return path + '.md';
  }

  // --- Fetch raw markdown ---

  function fetchMarkdown(path, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', RAW_BASE + path, true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        cb(null, xhr.responseText);
      } else {
        cb('Failed to load article content (HTTP ' + xhr.status + ')');
      }
    };
    xhr.onerror = function () { cb('Network error'); };
    xhr.send();
  }

  // --- Submit edit ---

  function submitEdit(data, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', API + '/submit-edit', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
      if (xhr.status === 200 || xhr.status === 201) {
        try {
          cb(null, JSON.parse(xhr.responseText));
        } catch (_) {
          cb(null, {});
        }
      } else {
        var msg = 'Submission failed';
        try {
          msg = JSON.parse(xhr.responseText).error || msg;
        } catch (_) {}
        cb(msg);
      }
    };
    xhr.onerror = function () { cb('Network error'); };
    xhr.send(JSON.stringify(data));
  }

  // --- Build modal ---

  function createModal() {
    var overlay = document.createElement('div');
    overlay.className = 'aw-edit-overlay';
    overlay.innerHTML =
      '<div class="aw-edit-modal">' +
        '<div class="aw-edit-header">' +
          '<h3>Suggest an Edit</h3>' +
          '<button class="aw-edit-close" title="Close">&times;</button>' +
        '</div>' +
        '<div class="aw-edit-body">' +
          '<div class="aw-edit-login-view">' +
            '<p>Sign in with GitHub to suggest edits to this article.</p>' +
            '<button class="aw-btn aw-btn-github">Sign in with GitHub</button>' +
          '</div>' +
          '<div class="aw-edit-editor-view" style="display:none">' +
            '<div class="aw-edit-user-bar">' +
              '<img class="aw-edit-avatar" src="" alt="">' +
              '<span class="aw-edit-username"></span>' +
              '<button class="aw-btn aw-btn-sm aw-btn-logout">Logout</button>' +
            '</div>' +
            '<div class="aw-edit-loading">Loading article content...</div>' +
            '<textarea class="aw-edit-textarea" style="display:none" spellcheck="false"></textarea>' +
            '<div class="aw-edit-actions" style="display:none">' +
              '<button class="aw-btn aw-btn-cancel">Cancel</button>' +
              '<button class="aw-btn aw-btn-submit">Submit Edit</button>' +
            '</div>' +
          '</div>' +
          '<div class="aw-edit-result" style="display:none"></div>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);
    return overlay;
  }

  // --- Modal logic ---

  function openModal() {
    var overlay = document.querySelector('.aw-edit-overlay') || createModal();
    var auth = getAuth();
    var articlePath = getArticlePath();
    var originalContent = '';

    var loginView = overlay.querySelector('.aw-edit-login-view');
    var editorView = overlay.querySelector('.aw-edit-editor-view');
    var resultView = overlay.querySelector('.aw-edit-result');
    var loadingEl = overlay.querySelector('.aw-edit-loading');
    var textarea = overlay.querySelector('.aw-edit-textarea');
    var actionsEl = overlay.querySelector('.aw-edit-actions');

    // Reset views
    loginView.style.display = 'none';
    editorView.style.display = 'none';
    resultView.style.display = 'none';
    loadingEl.style.display = 'block';
    textarea.style.display = 'none';
    actionsEl.style.display = 'none';
    textarea.value = '';
    resultView.innerHTML = '';

    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Close handlers
    overlay.querySelector('.aw-edit-close').onclick = closeModal;
    overlay.onclick = function (e) {
      if (e.target === overlay) closeModal();
    };

    if (!auth) {
      loginView.style.display = 'block';
      overlay.querySelector('.aw-btn-github').onclick = function () {
        var returnUrl = window.location.href.split('#')[0];
        window.location.href = API + '/auth/login?platform=web&return_url=' + encodeURIComponent(returnUrl);
      };
      return;
    }

    // Logged in
    editorView.style.display = 'block';
    var avatar = overlay.querySelector('.aw-edit-avatar');
    var username = overlay.querySelector('.aw-edit-username');
    avatar.src = auth.avatar_url || '';
    avatar.style.display = auth.avatar_url ? 'inline-block' : 'none';
    username.textContent = '@' + auth.login;

    overlay.querySelector('.aw-btn-logout').onclick = function () {
      clearAuth();
      closeModal();
    };

    overlay.querySelector('.aw-btn-cancel').onclick = closeModal;

    // Fetch content
    fetchMarkdown(articlePath, function (err, content) {
      loadingEl.style.display = 'none';
      if (err) {
        resultView.style.display = 'block';
        resultView.innerHTML = '<p class="aw-error">' + err + '</p>';
        return;
      }
      originalContent = content;
      textarea.value = content;
      textarea.style.display = 'block';
      actionsEl.style.display = 'flex';
    });

    // Submit
    overlay.querySelector('.aw-btn-submit').onclick = function () {
      var edited = textarea.value;
      if (edited === originalContent) {
        alert('No changes detected.');
        return;
      }

      var submitBtn = overlay.querySelector('.aw-btn-submit');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';

      // Derive article_id from path
      var articleId = articlePath.replace(/\.md$/, '').replace(/\/index$/, '');
      var title = document.querySelector('h1')?.textContent || articleId;

      submitEdit({
        article_id: articleId,
        article_title: title,
        original_content: originalContent,
        content: edited,
        github_token: auth.token,
        source: 'web'
      }, function (err, res) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Edit';

        if (err) {
          if (err.indexOf('401') !== -1 || err.indexOf('auth') !== -1 || err.indexOf('token') !== -1) {
            clearAuth();
            alert('Session expired. Please sign in again.');
            closeModal();
          } else {
            alert('Error: ' + err);
          }
          return;
        }

        textarea.style.display = 'none';
        actionsEl.style.display = 'none';
        resultView.style.display = 'block';
        var issueUrl = res.issue_url || '';
        resultView.innerHTML =
          '<p class="aw-success">Thank you! Your edit has been submitted for review.</p>' +
          (issueUrl ? '<p><a href="' + issueUrl + '" target="_blank" rel="noopener">View on GitHub &rarr;</a></p>' : '');
      });
    };
  }

  function closeModal() {
    var overlay = document.querySelector('.aw-edit-overlay');
    if (overlay) overlay.style.display = 'none';
    document.body.style.overflow = '';
  }

  // --- Tab-bar controls (Edit + sign-in) ---

  // System/meta pages and auto-generated section indexes are not user-editable.
  var SYSTEM_PAGES = {
    '': 1, 'index': 1, 'recent-changes': 1, 'credits': 1, 'contributing': 1,
    'privacy': 1, 'all-articles': 1, 'categories': 1
  };
  var SECTION_INDEXES = {
    'herbs': 1, 'medicines': 1, 'yoga': 1, 'concepts': 1, 'physiology': 1,
    'practices': 1, 'traditions': 1, 'manufacturers': 1, 'institutions': 1,
    'resources': 1, 'events': 1, 'gallery': 1, 'faqs': 1
  };

  function isArticlePage() {
    var path = window.location.pathname.replace(/^\//, '').replace(/\/$/, '');
    if (SYSTEM_PAGES[path]) return false;
    var segs = path.split('/');
    // A single-segment path that names a section is that section's index page.
    if (segs.length === 1 && SECTION_INDEXES[segs[0]]) return false;
    return !!document.querySelector('.md-content h1, article h1');
  }

  function startLogin() {
    var returnUrl = window.location.href.split('#')[0];
    window.location.href = API + '/auth/login?platform=web&return_url=' + encodeURIComponent(returnUrl);
  }

  // Find the Article/Contributors tab bar, or synthesize one on plain pages.
  function getTabBar() {
    var bar = document.querySelector('.aw-tab-bar');
    if (bar) return bar;
    var inner = document.querySelector('.md-content__inner');
    if (!inner) return null;
    bar = document.createElement('div');
    bar.className = 'aw-tab-bar aw-tab-bar--synth';
    inner.insertBefore(bar, inner.firstChild);
    return bar;
  }

  var EDIT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>';
  var GH_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5.99.11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.49 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58A12.01 12.01 0 0 0 24 12.5C24 5.87 18.63.5 12 .5z"/></svg>';

  function renderAuthChip(chip) {
    var auth = getAuth();
    chip.innerHTML = '';
    if (auth && auth.login) {
      if (auth.avatar_url) {
        var img = document.createElement('img');
        img.className = 'aw-auth-avatar';
        img.src = auth.avatar_url;
        img.alt = '';
        chip.appendChild(img);
      }
      var name = document.createElement('span');
      name.className = 'aw-auth-name';
      name.textContent = '@' + auth.login;
      chip.appendChild(name);
      var out = document.createElement('button');
      out.className = 'aw-auth-logout';
      out.textContent = 'Sign out';
      out.onclick = function () { clearAuth(); renderAuthChip(chip); };
      chip.appendChild(out);
    } else {
      var signin = document.createElement('button');
      signin.className = 'aw-tab aw-auth-signin';
      signin.innerHTML = GH_SVG + ' Sign in';
      signin.title = 'Sign in with GitHub';
      signin.onclick = startLogin;
      chip.appendChild(signin);
    }
  }

  function addEditButton() {
    if (!isArticlePage()) return;
    var bar = getTabBar();
    if (!bar || bar.querySelector('.aw-edit-tab')) return;

    // Edit button — grouped with the tabs (before Share if present)
    var editBtn = document.createElement('button');
    editBtn.className = 'aw-tab aw-edit-tab';
    editBtn.title = 'Suggest an edit';
    editBtn.innerHTML = EDIT_SVG + ' Edit';
    editBtn.onclick = openModal;
    var share = bar.querySelector('.aw-share-btn');
    if (share) bar.insertBefore(editBtn, share);
    else bar.appendChild(editBtn);

    // Auth chip — far right
    var chip = document.createElement('span');
    chip.className = 'aw-auth-chip';
    bar.appendChild(chip);
    renderAuthChip(chip);

    // Any in-content "Help complete it" triggers open the same modal.
    var triggers = document.querySelectorAll('.aw-edit-trigger');
    for (var t = 0; t < triggers.length; t++) triggers[t].onclick = openModal;
  }

  // --- Init ---

  function init() {
    var justLoggedIn = handleAuthCallback();
    // Wait for page content to load (MkDocs instant navigation)
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        addEditButton();
        if (justLoggedIn) openModal();
      });
    } else {
      addEditButton();
      if (justLoggedIn) openModal();
    }
  }

  // Handle MkDocs Material instant navigation
  if (typeof document$ !== 'undefined') {
    document$.subscribe(function () {
      // Clean up synthesized bars / injected controls from the previous page
      var synth = document.querySelector('.aw-tab-bar--synth');
      if (synth) synth.remove();
      var oldOverlay = document.querySelector('.aw-edit-overlay');
      if (oldOverlay) oldOverlay.remove();
      addEditButton();
    });
  }

  init();
})();
