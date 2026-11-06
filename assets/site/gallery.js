// "Some of Our Work": swaps GoSite's 2-up gallery slider for the shared MRSlider (same scrubber
// as the reviews) with a simple click-to-enlarge lightbox. Photos come from the mirrored gallery.
(function () {
  var css = document.createElement("style");
  css.textContent = [
    ".mr-gallery{max-width:1164px;margin:0 auto;padding:0 16px;box-sizing:border-box}",
    ".mr-photo{display:block;padding:0;border:0;background:#eee;cursor:zoom-in;aspect-ratio:4/3;overflow:hidden}",
    ".mr-photo img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s ease}",
    ".mr-photo:hover img{transform:scale(1.04)}",
    ".mr-lightbox{position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:16px}",
    ".mr-lightbox img{max-width:100%;max-height:88vh;object-fit:contain;box-shadow:0 10px 40px rgba(0,0,0,.5)}",
    ".mr-lb-btn{position:absolute;background:rgba(255,255,255,.12);color:#fff;border:0;border-radius:50%;width:46px;height:46px;font-size:26px;line-height:46px;cursor:pointer}",
    ".mr-lb-btn:hover{background:rgba(255,255,255,.25)}",
    ".mr-lb-close{top:14px;right:14px;font-size:20px}",
    ".mr-lb-prev{left:14px;top:50%;margin-top:-23px}.mr-lb-next{right:14px;top:50%;margin-top:-23px}",
    ".mr-lb-count{position:absolute;bottom:16px;left:0;right:0;text-align:center;color:#fff;font:600 13px Manrope,sans-serif}",
  ].join("\n");
  document.head.appendChild(css);

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function lightbox(urls, start) {
    var i = start;
    var ov = el("div", "mr-lightbox");
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    var img = el("img"), count = el("div", "mr-lb-count");
    var close = el("button", "mr-lb-btn mr-lb-close", "✕"), prev = el("button", "mr-lb-btn mr-lb-prev", "‹"), next = el("button", "mr-lb-btn mr-lb-next", "›");
    close.setAttribute("aria-label", "Close");
    prev.setAttribute("aria-label", "Previous photo");
    next.setAttribute("aria-label", "Next photo");
    function show() {
      img.src = urls[i];
      img.alt = "Magnolia Roofing project photo " + (i + 1);
      count.textContent = (i + 1) + " of " + urls.length;
    }
    function move(d) { i = (i + d + urls.length) % urls.length; show(); }
    function shut() { ov.remove(); document.removeEventListener("keydown", key); }
    function key(e) {
      if (e.key === "Escape") shut();
      else if (e.key === "ArrowLeft") move(-1);
      else if (e.key === "ArrowRight") move(1);
    }
    prev.addEventListener("click", function (e) { e.stopPropagation(); move(-1); });
    next.addEventListener("click", function (e) { e.stopPropagation(); move(1); });
    ov.addEventListener("click", function (e) { if (e.target === ov || e.target === close) shut(); });
    document.addEventListener("keydown", key);
    [img, close, prev, next, count].forEach(function (n) { ov.appendChild(n); });
    show();
    document.body.appendChild(ov);
  }

  // assets/site/work.json lists the photos in display order (mirrored GoSite photos not in it go last).
  var extra = [];
  function start() {
    fetch("/assets/site/work.json")
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (list) { extra = list || []; })
      .catch(function () {})
      .then(build);
  }

  function build() {
    var heading = [].find.call(document.querySelectorAll("h1,h2,h3"), function (h) {
      return /^Some of Our Work/.test(h.textContent.trim());
    });
    if (!heading) return;
    // first Gallery widget after the heading
    var gallery = [].find.call(document.querySelectorAll('[data-type="Gallery"]'), function (g) {
      return heading.compareDocumentPosition(g) & Node.DOCUMENT_POSITION_FOLLOWING;
    });
    if (!gallery) return;

    var urls = [];
    gallery.querySelectorAll("[data-slide]").forEach(function (n) {
      var u = n.getAttribute("data-slide");
      if (u && urls.indexOf(u) < 0) urls.push(u);
    });
    // work.json sets the display order (it can list mirrored photos too); anything it leaves out goes last
    var rest = urls.filter(function (u) { return extra.indexOf(u) < 0; });
    urls = extra.slice().concat(rest);
    if (!urls.length) return;

    var wrap = el("div", "mr-gallery");
    var photos = urls.map(function (u, i) {
      var b = el("button", "mr-photo");
      b.type = "button";
      b.setAttribute("aria-label", "Enlarge project photo " + (i + 1));
      var img = el("img");
      img.src = u;
      img.alt = "Magnolia Roofing project photo " + (i + 1);
      img.loading = "lazy";
      b.appendChild(img);
      b.addEventListener("click", function () { lightbox(urls, i); });
      return b;
    });
    var slider = window.MRSlider(wrap, photos, { noun: "project photos" });

    var inner = gallery.querySelector(".inline-gallery") || gallery.firstElementChild;
    inner.style.display = "none";
    inner.parentNode.insertBefore(wrap, inner);
    slider.init();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
