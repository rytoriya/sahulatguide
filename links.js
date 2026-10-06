/*
 * Sahulat Guide: every link to another website gets rel="nofollow"
 * (plus "noopener" when it opens in a new tab). Links to this site are left alone.
 * Loaded on every page by the shared footer (partials/footer.html). It also covers
 * links that page scripts add later (news, maps, directories), so nothing is missed.
 * Links written in the HTML are already marked by scripts/nofollow_links.js.
 */
(function () {
  "use strict";
  if (window.__sgLinks) return;
  window.__sgLinks = true;
  var OWN = /(^|\.)sahulatguide\.(netlify\.app|pk)$/i;

  function fix(a) {
    var href = a.getAttribute("href"), u;
    if (!href) return;
    try { u = new URL(href, location.href); } catch (e) { return; }
    if (!/^https?:$/.test(u.protocol) || u.hostname === location.hostname || OWN.test(u.hostname)) return;
    var rel = (a.getAttribute("rel") || "").split(/\s+/).filter(Boolean);
    var changed = false;
    if (rel.indexOf("nofollow") < 0) { rel.unshift("nofollow"); changed = true; }
    if (a.target === "_blank" && rel.indexOf("noopener") < 0) { rel.push("noopener"); changed = true; }
    if (changed) a.setAttribute("rel", rel.join(" "));
  }
  function scan(node) {
    if (node.nodeType !== 1) return;
    if (node.tagName === "A") fix(node);
    var list = node.querySelectorAll ? node.querySelectorAll("a[href]") : [];
    for (var i = 0; i < list.length; i++) fix(list[i]);
  }

  scan(document.documentElement);
  new MutationObserver(function (records) {
    for (var i = 0; i < records.length; i++) {
      var r = records[i];
      if (r.type === "attributes") fix(r.target);
      else for (var j = 0; j < r.addedNodes.length; j++) scan(r.addedNodes[j]);
    }
  }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["href"] });
})();
