// "What Our Clients Say": replaces the two static cards with a scrolling row of every review
// (assets/site/reviews.json, refreshed by tools/mirror.py), plus a "Leave Feedback" modal
// that emails Name + star rating + date through the same service as the contact form.
(function () {
  var C = window.SITE_CONFIG || {};
  var MAROON = "rgb(80, 21, 40)", BUTTON = "#72213b";

  var css = document.createElement("style");
  css.textContent = [
    ".mr-reviews{position:relative;z-index:2;max-width:1164px;margin:0 auto;padding:0 16px;box-sizing:border-box;font-family:Manrope,sans-serif;color:#fff}",
    ".mr-reviews-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 18px}",
    ".mr-reviews-summary{font-size:15px;letter-spacing:.3px}",
    ".mr-reviews-summary b{font-family:'PT Serif',serif;font-size:22px;margin-right:6px}",
    ".mr-stars{color:#f5b301;letter-spacing:2px}",
    ".mr-reviews-actions{display:flex;gap:8px;align-items:center}",
    ".mr-btn{font:700 14px/1 Manrope,sans-serif;letter-spacing:1px;border:0;border-radius:5px;padding:13px 22px;cursor:pointer;background:#fff;color:" + BUTTON + "}",
    ".mr-arrow{width:42px;height:42px;border-radius:50%;border:1px solid rgba(255,255,255,.6);background:transparent;color:#fff;font-size:18px;cursor:pointer}",
    ".mr-arrow:hover,.mr-btn:hover{opacity:.85}",
    ".mr-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;padding-bottom:12px;scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.5) transparent}",
    ".mr-card{flex:0 0 calc((100% - 40px)/3);min-width:270px;box-sizing:border-box;scroll-snap-align:start;background:" + MAROON + ";border:1px solid rgba(255,255,255,.35);padding:26px 28px;display:flex;flex-direction:column;height:300px}",
    ".mr-card-text{flex:1;overflow-y:auto;font-size:14px;line-height:1.6;margin:10px 0 14px;padding-right:6px;white-space:pre-line;scrollbar-width:thin}",
    ".mr-card-name{font-family:'PT Serif',serif;font-weight:700;font-size:20px}",
    ".mr-card-meta{font-size:12px;opacity:.8;margin-top:2px}",
    "@media (max-width:640px){.mr-card{flex-basis:85%}.mr-arrow{display:none}}",
    // modal
    ".mr-modal{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:16px}",
    ".mr-modal-box{background:#fff;color:#222;width:100%;max-width:420px;border-radius:8px;padding:30px;position:relative;font-family:Manrope,sans-serif;box-sizing:border-box}",
    ".mr-modal-box h3{font-family:'PT Serif',serif;font-size:24px;margin:0 0 18px;color:" + BUTTON + "}",
    ".mr-modal-box label{display:block;font-size:14px;margin:0 0 6px}",
    ".mr-modal-box input{width:100%;box-sizing:border-box;border:1px solid #c9c9c9;border-radius:5px;padding:11px;font:15px Manrope,sans-serif;margin-bottom:18px}",
    ".mr-pick{display:flex;gap:4px;margin-bottom:22px}",
    ".mr-pick button{background:none;border:0;padding:0 2px;font-size:34px;line-height:1;cursor:pointer;color:#ccc}",
    ".mr-pick button.on{color:#f5b301}",
    ".mr-err{color:#e25141;font-size:13px;margin:-10px 0 14px;display:none}",
    ".mr-close{position:absolute;top:10px;right:14px;border:0;background:none;font-size:22px;cursor:pointer}",
    ".mr-modal .mr-btn{background:" + BUTTON + ";color:#fff;width:100%}",
  ].join("\n");
  document.head.appendChild(css);

  function stars(n) { return "★★★★★".slice(0, n) + "☆☆☆☆☆".slice(0, 5 - n); }
  function fmtDate(iso) {
    var d = new Date(iso + "T12:00:00");
    return isNaN(d) ? "" : d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  /* ---------- Feedback modal ---------- */
  function openFeedback() {
    var rating = 0;
    var ov = el("div", "mr-modal");
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    var box = el("div", "mr-modal-box");
    var close = el("button", "mr-close", "✕");
    close.setAttribute("aria-label", "Close");
    box.appendChild(close);
    box.appendChild(el("h3", null, "Leave Feedback"));

    box.appendChild(el("label", null, "Name"));
    var name = el("input");
    name.type = "text";
    name.placeholder = "John Hasaleak";
    box.appendChild(name);

    box.appendChild(el("label", null, "Rating"));
    var pick = el("div", "mr-pick");
    var btns = [1, 2, 3, 4, 5].map(function (n) {
      var b = el("button", null, "★");
      b.type = "button";
      b.setAttribute("aria-label", n + " star" + (n > 1 ? "s" : ""));
      b.addEventListener("click", function () { rating = n; paint(n); });
      b.addEventListener("mouseenter", function () { paint(n); });
      pick.appendChild(b);
      return b;
    });
    pick.addEventListener("mouseleave", function () { paint(rating); });
    function paint(n) { btns.forEach(function (b, i) { b.classList.toggle("on", i < n); }); }
    box.appendChild(pick);

    var err = el("div", "mr-err", "Please enter your name and pick a star rating.");
    box.appendChild(err);
    var send = el("button", "mr-btn", "SUBMIT FEEDBACK");
    send.type = "button";
    box.appendChild(send);

    function shut() { ov.remove(); document.removeEventListener("keydown", esc); }
    function esc(e) { if (e.key === "Escape") shut(); }
    ov.addEventListener("click", function (e) { if (e.target === ov || e.target === close) shut(); });
    document.addEventListener("keydown", esc);

    send.addEventListener("click", function () {
      var n = name.value.trim();
      if (!n || !rating) { err.style.display = "block"; return; }
      err.style.display = "none";
      send.disabled = true;
      send.textContent = "SENDING…";
      var date = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      window.SiteEmail("Website feedback: " + rating + " star" + (rating > 1 ? "s" : "") + " from " + n,
        { Name: n, Rating: stars(rating) + " (" + rating + "/5)", Date: date })
        .then(function () {
          box.innerHTML = "";
          box.appendChild(close);
          box.appendChild(el("h3", null, "Thank you!"));
          box.appendChild(el("p", null, "We appreciate you taking the time to leave feedback."));
        })
        .catch(function () {
          send.disabled = false;
          send.textContent = "SUBMIT FEEDBACK";
          err.textContent = "Sorry, that didn't go through. Please call us at (803) 908-7131.";
          err.style.display = "block";
        });
    });

    ov.appendChild(box);
    document.body.appendChild(ov);
    name.focus({ preventScroll: true });
  }

  /* ---------- Reviews row ---------- */
  function build(reviews) {
    // Locate the two static cards by their author headings and swap their row for ours.
    var heads = [].filter.call(document.querySelectorAll('[data-type="HeadingWidget"]'), function (h) {
      return /^(Jason R\.|Whitney D\.)$/.test(h.textContent.trim());
    });
    if (heads.length < 2) return;
    var row = heads[0];
    while (row && !row.contains(heads[1])) row = row.parentElement;
    if (!row) return;

    var wrap = el("div", "mr-reviews");
    var bar = el("div", "mr-reviews-bar");
    var sum = el("div", "mr-reviews-summary");
    var avg = reviews.reduce(function (s, r) { return s + r.rating; }, 0) / reviews.length;
    sum.appendChild(el("b", null, avg.toFixed(1)));
    sum.appendChild(el("span", "mr-stars", stars(Math.round(avg))));
    sum.appendChild(document.createTextNode("  Based on " + reviews.length + " reviews"));
    bar.appendChild(sum);

    var actions = el("div", "mr-reviews-actions");
    var prev = el("button", "mr-arrow", "‹"), next = el("button", "mr-arrow", "›");
    prev.setAttribute("aria-label", "Previous reviews");
    next.setAttribute("aria-label", "Next reviews");
    var fb = el("button", "mr-btn", "LEAVE FEEDBACK");
    fb.addEventListener("click", openFeedback);
    actions.appendChild(prev);
    actions.appendChild(next);
    actions.appendChild(fb);
    bar.appendChild(actions);
    wrap.appendChild(bar);

    var track = el("div", "mr-track");
    track.setAttribute("tabindex", "0");
    track.setAttribute("aria-label", "Customer reviews");
    reviews.forEach(function (r) {
      var c = el("div", "mr-card");
      c.appendChild(el("div", "mr-stars", stars(r.rating)));
      c.appendChild(el("div", "mr-card-text", r.text || "★ Rated " + r.rating + " stars"));
      c.appendChild(el("div", "mr-card-name", r.name));
      c.appendChild(el("div", "mr-card-meta", fmtDate(r.date) + (r.source === "FACEBOOK" ? " · Facebook" : " · Google")));
      track.appendChild(c);
    });
    wrap.appendChild(track);

    function page(dir) { track.scrollBy({ left: dir * track.clientWidth, behavior: "smooth" }); }
    prev.addEventListener("click", function () { page(-1); });
    next.addEventListener("click", function () { page(1); });

    row.style.display = "none";
    row.parentNode.insertBefore(wrap, row);
  }

  fetch("/assets/site/reviews.json")
    .then(function (r) { return r.json(); })
    .then(build)
    .catch(function (e) { console.warn("reviews:", e); });
})();
