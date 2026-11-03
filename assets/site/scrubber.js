// Shared horizontal slider: a snap-scrolling track of items + a burgundy "scrubber" pill.
//   MRSlider(container, items, opts) -> appends .mr-track and .mr-scrub to container.
//   items: array of DOM nodes (each becomes one slide; 3 per page desktop, 1 on phones).
//   opts.markers: optional [{label, index}] shown as tappable steps under the rail (e.g. years).
//   opts.noun:   word for the aria label ("reviews", "photos").
// Dragging the pill steps one page; the label shows "4–6 of 13"; arrow/Home/End keys work;
// the thumb follows swipes on the track.
(function () {
  var MAROON = "rgb(80, 21, 40)", BUTTON = "#72213b", GAP = 20;

  var css = document.createElement("style");
  css.textContent = [
    ".mr-track{display:flex;gap:" + GAP + "px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;-ms-overflow-style:none}",
    ".mr-track::-webkit-scrollbar{display:none}",
    ".mr-track>*{flex:0 0 calc((100% - " + 2 * GAP + "px)/3);box-sizing:border-box;scroll-snap-align:start}",
    "@media (max-width:767px){.mr-track>*{flex-basis:100%}}",
    // pill: solid burgundy so it reads on any background (incl. the white section curves)
    ".mr-scrub{position:relative;width:min(460px,92%);height:38px;margin:26px auto 0;border-radius:999px;background:" + MAROON + ";border:1px solid rgba(255,255,255,.35);box-shadow:0 4px 14px rgba(0,0,0,.25);touch-action:none;user-select:none;-webkit-user-select:none;outline:none;font-family:Manrope,sans-serif}",
    ".mr-scrub.has-markers{height:56px}",
    ".mr-scrub:focus-visible{box-shadow:0 0 0 3px rgba(255,255,255,.6),0 0 0 5px " + BUTTON + "}",
    ".mr-scrub-hit{position:absolute;left:0;right:0;top:0;height:38px;cursor:pointer}",
    ".mr-scrub.has-markers .mr-scrub-hit{height:30px}",
    ".mr-scrub-rail{position:absolute;left:22px;right:22px;top:17px;height:4px;border-radius:2px;background:rgba(255,255,255,.25);pointer-events:none}",
    ".mr-scrub-thumb{position:absolute;top:50%;height:12px;margin-top:-6px;border-radius:6px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.35);transition:left .25s ease,width .25s ease}",
    ".mr-scrub.dragging .mr-scrub-thumb{transition:none;height:16px;margin-top:-8px}",
    ".mr-scrub-tick{position:absolute;top:-3px;width:2px;height:10px;margin-left:-1px;border-radius:1px;background:rgba(255,255,255,.55)}",
    ".mr-scrub-label{position:absolute;bottom:calc(100% + 24px);transform:translateX(-50%);background:#fff;color:" + BUTTON + ";font:700 12px/1 Manrope,sans-serif;padding:6px 9px;border-radius:999px;white-space:nowrap;opacity:0;transition:opacity .15s;pointer-events:none;box-shadow:0 2px 6px rgba(0,0,0,.25)}",
    ".mr-scrub.dragging .mr-scrub-label,.mr-scrub:hover .mr-scrub-label,.mr-scrub:focus-visible .mr-scrub-label{opacity:1}",
    ".mr-scrub-marks{position:absolute;left:22px;right:22px;top:30px;height:18px}",
    ".mr-mark{position:absolute;transform:translateX(-50%);background:none;border:0;padding:2px 3px;font:600 11px/1 Manrope,sans-serif;color:rgba(255,255,255,.7);cursor:pointer;white-space:nowrap}",
    ".mr-mark:hover,.mr-mark.on{color:#fff}",
    ".mr-mark.on{font-weight:800}",
  ].join("\n");
  document.head.appendChild(css);

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  window.MRSlider = function (container, items, opts) {
    opts = opts || {};
    var N = items.length, markers = opts.markers || [];

    var track = el("div", "mr-track");
    track.setAttribute("tabindex", "0");
    track.setAttribute("aria-label", opts.noun || "items");
    items.forEach(function (n) { track.appendChild(n); });
    container.appendChild(track);

    var scrub = el("div", "mr-scrub" + (markers.length ? " has-markers" : ""));
    scrub.setAttribute("role", "slider");
    scrub.setAttribute("tabindex", "0");
    scrub.setAttribute("aria-label", "Browse " + (opts.noun || "items"));
    var hit = el("div", "mr-scrub-hit"), rail = el("div", "mr-scrub-rail"), thumb = el("div", "mr-scrub-thumb"),
        label = el("div", "mr-scrub-label"), marks = el("div", "mr-scrub-marks");
    rail.appendChild(thumb);
    rail.appendChild(label);
    scrub.appendChild(rail);
    scrub.appendChild(hit);
    if (markers.length) scrub.appendChild(marks);
    container.appendChild(scrub);

    function step() { return track.firstChild.offsetWidth + GAP; }
    function perPage() { return Math.max(1, Math.round((track.clientWidth + GAP) / step())); }
    function maxStart() { return Math.max(0, N - perPage()); }
    function current() { return Math.min(maxStart(), Math.round(track.scrollLeft / step())); }
    function go(i, instant) {
      i = Math.max(0, Math.min(maxStart(), i));
      // smooth only for short hops; long jumps (years, far drags) would crawl
      var far = Math.abs(i - current()) > perPage() * 2;
      track.scrollTo({ left: i * step(), behavior: instant || far ? "instant" : "smooth" });
      return i;
    }
    function frac(i) { return maxStart() ? Math.min(1, i / maxStart()) : 0; }
    function thumbWidth() { return Math.max(26, rail.clientWidth * Math.min(1, perPage() / N)); }

    function layoutMarkers() {
      [].slice.call(rail.querySelectorAll(".mr-scrub-tick")).forEach(function (x) { x.remove(); });
      marks.innerHTML = "";
      var w = rail.clientWidth, tw = thumbWidth(), lastX = -1e9;
      markers.forEach(function (m) {
        var x = (w - tw) * frac(m.index) + tw / 2;
        var tick = el("div", "mr-scrub-tick");
        tick.style.left = x + "px";
        rail.appendChild(tick);
        if (x - lastX < 34) return; // label would collide with the previous one; keep just the tick
        lastX = x;
        var b = el("button", "mr-mark", m.label);
        b.type = "button";
        b.dataset.index = m.index;
        b.style.left = x + "px";
        b.setAttribute("aria-label", "Jump to " + m.label);
        b.addEventListener("click", function () { paint(go(m.index)); });
        marks.appendChild(b);
      });
    }
    function markerFor(i) {
      var cur = null;
      markers.forEach(function (m) { if (m.index <= i) cur = m; });
      return cur;
    }

    var shown = 0;
    function paint(i) {
      var w = rail.clientWidth, tw = thumbWidth(), x = (w - tw) * frac(i), pp = perPage();
      thumb.style.width = tw + "px";
      thumb.style.left = x + "px";
      label.style.left = x + tw / 2 + "px";
      var last = Math.min(N, i + pp);
      label.textContent = (last > i + 1 ? (i + 1) + "–" + last : i + 1) + " of " + N;
      var m = markerFor(i);
      [].forEach.call(marks.children, function (b) { b.classList.toggle("on", !!m && b.textContent === m.label); });
      scrub.setAttribute("aria-valuemin", "1");
      scrub.setAttribute("aria-valuemax", String(N));
      scrub.setAttribute("aria-valuenow", String(i + 1));
      scrub.setAttribute("aria-valuetext", label.textContent + (m ? ", " + m.label : ""));
      shown = i;
    }
    function startAt(clientX) {
      var r = rail.getBoundingClientRect(), pp = perPage(), ms = maxStart();
      var f = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
      return Math.min(ms, Math.round((f * ms) / pp) * pp); // snap to page steps
    }

    var dragging = false;
    hit.addEventListener("pointerdown", function (e) {
      dragging = true;
      scrub.classList.add("dragging");
      hit.setPointerCapture(e.pointerId);
      paint(go(startAt(e.clientX)));
    });
    hit.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var i = startAt(e.clientX);
      if (i !== shown) paint(go(i, true));
    });
    function end() {
      if (!dragging) return;
      dragging = false;
      scrub.classList.remove("dragging");
      go(shown, true); // land exactly on the page in the label
    }
    hit.addEventListener("pointerup", end);
    hit.addEventListener("pointercancel", end);

    function keys(e) {
      var i = shown, pp = perPage();
      if (e.key === "ArrowRight") i += pp;
      else if (e.key === "ArrowLeft") i -= pp;
      else if (e.target === scrub && e.key === "ArrowUp") i += pp;
      else if (e.target === scrub && e.key === "ArrowDown") i -= pp;
      else if (e.key === "Home") i = 0;
      else if (e.key === "End") i = maxStart();
      else return;
      e.preventDefault();
      paint(go(i));
    }
    scrub.addEventListener("keydown", keys);
    track.addEventListener("keydown", keys);

    var t;
    track.addEventListener("scroll", function () {
      if (dragging) return;
      clearTimeout(t);
      t = setTimeout(function () { paint(current()); }, 60);
    });
    window.addEventListener("resize", function () { layoutMarkers(); paint(current()); });

    return {
      track: track,
      scrub: scrub,
      // call once the container is in the document (sizes are needed)
      init: function () { layoutMarkers(); paint(0); },
      go: function (i) { paint(go(i)); },
    };
  };
})();
