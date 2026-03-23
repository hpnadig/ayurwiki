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
    if (!hash || hash.indexOf('token=') === -1) return;

    var params = new URLSearchParams(hash.substring(1));
    var token = params.get('token');
    var error = params.get('auth_error');

    if (error) {
      alert('Login failed: ' + error);
      history.replaceState(null, '', window.location.pathname + window.location.search);
      return;
    }

    if (token) {
      setAuth({
        token: token,
        login: params.get('login') || '',
        name: params.get('name') || '',
        avatar_url: params.get('avatar_url') || ''
      });
      history.replaceState(null, '', window.location.pathname + window.location.search);
    }
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

  // --- Floating button ---

  function addEditButton() {
    // Don't add on index/home pages
    var path = window.location.pathname.replace(/^\//, '').replace(/\/$/, '');
    if (!path || path === '' || path === 'index') return;
    // Don't add if no h1 (not an article page)
    if (!document.querySelector('article h1, .md-content h1')) return;

    var btn = document.createElement('button');
    btn.className = 'aw-edit-fab';
    btn.title = 'Suggest an edit';
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>';
    btn.onclick = openModal;
    document.body.appendChild(btn);
  }

  // --- Init ---

  function init() {
    handleAuthCallback();
    // Wait for page content to load (MkDocs instant navigation)
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', addEditButton);
    } else {
      addEditButton();
    }
  }

  // Handle MkDocs Material instant navigation
  if (typeof document$ !== 'undefined') {
    document$.subscribe(function () {
      // Remove old FAB on navigation
      var oldFab = document.querySelector('.aw-edit-fab');
      if (oldFab) oldFab.remove();
      var oldOverlay = document.querySelector('.aw-edit-overlay');
      if (oldOverlay) oldOverlay.remove();
      addEditButton();
    });
  }

  init();
})();
