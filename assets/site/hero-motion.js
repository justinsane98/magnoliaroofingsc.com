/* Hero "drone" motion: 3 aerial shots, slow Ken Burns zoom + subtle pan, crossfading in a loop.
   Runs only when <html data-hero-motion> is set (see /preview/hero-motion/).
   Each shot can be a still (src) or, later, a real drone clip (video: "/path.mp4", poster: src). */
(function () {
  if (!document.documentElement.hasAttribute("data-hero-motion")) return;
  var SHOTS = [
    { src: "/assets/site/hero-motion/shot-1.jpg", from: "1.04", to: "1.16", tx: "-2.5%", ty: "-1.5%" },
    { src: "/assets/site/hero-motion/shot-2.jpg", from: "1.16", to: "1.05", tx: "2.5%", ty: "1%" },
    { src: "/assets/site/hero-motion/shot-3.jpg", from: "1.05", to: "1.17", tx: "1.5%", ty: "-2%" }
  ];
  // random opening shot on each load (rotate the list so the order stays 1→2→3)
  var k = parseInt(document.documentElement.getAttribute("data-hero-shot"), 10); // picked inline in the hero (no flash)
  if (!(k >= 0 && k < SHOTS.length)) k = Math.floor(Math.random() * SHOTS.length);
  SHOTS = SHOTS.slice(k).concat(SHOTS.slice(0, k));
  var SECS = 10.5, FADE = 1.8; // per shot / crossfade (slowed by a third from 7s / 1.2s)

  var hero = document.querySelector(".mr-hero");
  if (!hero) return; // sits under the colour overlay (z 1) and the text (z 2); GoSite rebuilds .parallax-bg, so not in there
  var cyc = SHOTS.length * SECS, fade = (FADE / cyc * 100).toFixed(2), hold = (SECS / cyc * 100).toFixed(2),
      out = ((SECS + FADE) / cyc * 100).toFixed(2);
  var css =
    ".mr-motion{position:absolute;inset:0;overflow:hidden;z-index:0;background:transparent}" +
    ".mr-shot{position:absolute;inset:0;opacity:0;will-change:opacity,transform;" +
    "animation:mr-shot-fade " + cyc + "s linear infinite,mr-shot-move " + cyc + "s linear infinite}" +
    ".mr-shot img,.mr-shot video{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(1.2) contrast(1.06)}" +
    "@keyframes mr-shot-fade{0%{opacity:0}" + fade + "%{opacity:1}" + hold + "%{opacity:1}" + out + "%{opacity:0}100%{opacity:0}}" +
    "@keyframes mr-shot-move{0%{transform:scale(var(--from)) translate(0,0)}" + out + "%{transform:scale(var(--to)) translate(var(--tx),var(--ty))}100%{transform:scale(var(--to)) translate(var(--tx),var(--ty))}}" +
    "@media (prefers-reduced-motion:reduce){.mr-shot{animation:none}.mr-shot:first-child{opacity:1}}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var later = [];
  var wrap = document.createElement("div");
  wrap.className = "mr-motion"; wrap.setAttribute("aria-hidden", "true");
  SHOTS.forEach(function (s, i) {
    var d = document.createElement("div");
    d.className = "mr-shot";
    d.style.cssText = "--from:" + s.from + ";--to:" + s.to + ";--tx:" + s.tx + ";--ty:" + s.ty + ";animation-delay:" + (i * SECS - FADE) + "s," + (i * SECS - FADE) + "s"; // shifted by FADE so shot 1 is already fully in on load
    var m;
    if (s.video) {
      m = document.createElement("video");
      m.muted = true; m.autoplay = true; m.loop = true; m.playsInline = true; m.preload = i ? "metadata" : "auto";
      m.poster = s.src; m.src = s.video;
    } else {
      m = document.createElement("img"); m.alt = "";
      if (!i) { m.fetchPriority = "high"; m.decoding = "sync"; m.src = s.src; } // preloaded from <head>
      else { m.decoding = "async"; later.push([m, s.src]); } // not on screen for ~9 s: load once the page is done
    }
    d.appendChild(m); wrap.appendChild(d);
  });
  hero.insertBefore(wrap, hero.querySelector(".background-overlay") || null);
  var started = false, first = wrap.querySelector("img");
  function loadRest() { if (started) return; started = true; later.forEach(function (p) { p[0].src = p[1]; }); }
  function afterFirst() { // never compete with the opening shot (the LCP image) for bandwidth
    if (document.readyState === "complete") loadRest();
    else { window.addEventListener("load", loadRest); setTimeout(loadRest, 2500); } // whichever comes first
  }
  if (!first || first.complete) afterFirst();
  else { first.addEventListener("load", afterFirst); first.addEventListener("error", afterFirst); }

  /* Overlay colour variants, preview page only: ?overlay=live|warm|red|green|black, plus a small switcher.
     The live overlay itself is in site.css (.mr-hero .background-overlay). */
  if (!/^\/preview\//.test(location.pathname)) return;
  var OVERLAYS = {
    live: "linear-gradient(180deg, rgba(0,0,0,.40) 0%, rgba(0,0,0,.24) 30%, rgba(0,0,0,.18) 50%, rgba(115,33,59,.30) 75%, rgba(90,26,46,.47) 100%)",
    warm: "linear-gradient(180deg, rgba(25,10,18,.55) 0%, rgba(25,10,18,.22) 38%, rgba(115,33,59,.30) 72%, rgba(232,150,52,.38) 100%)",
    red: "linear-gradient(180deg, rgba(58,16,30,.62) 0%, rgba(115,33,59,.28) 40%, rgba(115,33,59,.50) 75%, rgba(90,26,46,.72) 100%)",
    green: "linear-gradient(180deg, rgba(0,38,25,.62) 0%, rgba(0,107,70,.24) 40%, rgba(0,107,70,.42) 75%, rgba(0,60,40,.70) 100%)",
    black: "linear-gradient(180deg, rgba(0,0,0,.58) 0%, rgba(0,0,0,.22) 40%, rgba(0,0,0,.34) 75%, rgba(0,0,0,.62) 100%)"
  };
  var ov = hero.querySelector(".background-overlay");
  function setOverlay(k) {
    if (!ov || !OVERLAYS[k]) return;
    ov.style.setProperty("background", OVERLAYS[k], "important");
    [].forEach.call(document.querySelectorAll(".mr-ov-switch button"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.k === k)); });
    try { history.replaceState(null, "", "?overlay=" + k); } catch (e) {}
  }
  var sw = document.createElement("div");
  sw.className = "mr-ov-switch";
  sw.innerHTML = "<span>Overlay</span>" + Object.keys(OVERLAYS).map(function (k) { return '<button type="button" data-k="' + k + '">' + k + "</button>"; }).join("");
  var st2 = document.createElement("style");
  st2.textContent = ".mr-ov-switch{position:fixed;left:16px;bottom:16px;z-index:99999;display:flex;gap:6px;align-items:center;background:#fff;padding:8px 10px;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.25);font:700 12px Manrope,sans-serif;text-transform:uppercase;letter-spacing:.5px}" +
    ".mr-ov-switch span{color:#5b6169;margin-right:4px}.mr-ov-switch button{font:inherit;text-transform:inherit;border:1px solid #e7e1e3;background:#fff;color:#1f232b;border-radius:8px;padding:7px 10px;cursor:pointer}" +
    ".mr-ov-switch button[aria-pressed=true]{background:#1f232b;color:#fff;border-color:#1f232b}";
  document.head.appendChild(st2);
  document.body.appendChild(sw);
  sw.addEventListener("click", function (e) { var b = e.target.closest("button"); if (b) setOverlay(b.dataset.k); });
  var q = (location.search.match(/overlay=(\w+)/) || [])[1];
  setOverlay(OVERLAYS[q] ? q : "live");
})();
