/**
 * Share button handler — copies short URL to clipboard or opens native share.
 */
(function () {
  function initShare() {
    document.querySelectorAll(".aw-share-btn").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();

        var shortPath = btn.getAttribute("data-short-url");
        var fullUrl = location.origin + shortPath;

        // Try native share on mobile
        if (navigator.share) {
          navigator.share({ title: document.title, url: fullUrl }).catch(function () {});
          return;
        }

        // Fallback: copy to clipboard
        navigator.clipboard.writeText(fullUrl).then(function () {
          btn.classList.add("aw-copied");
          btn.setAttribute("data-tooltip", "Copied!");
          setTimeout(function () {
            btn.classList.remove("aw-copied");
          }, 2000);
        });
      });
    });
  }

  // Support MkDocs Material instant navigation
  if (typeof document$ !== "undefined") {
    document$.subscribe(function () { initShare(); });
  } else {
    document.addEventListener("DOMContentLoaded", initShare);
  }
})();
