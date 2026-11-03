// Home hero: "The State's Best" 2025 + 2026 winner badges (assets/site/badges/the-states-best-<year>.png).
// The images include some background; site.css clips them to the badge outline (.mr-badge img).
(function () {
  var hero = document.querySelector(".mr-hero");
  var h1 = hero && hero.querySelector("h1");
  if (!h1 || !/Reroof/i.test(h1.textContent)) return; // home page hero only

  var BADGES = [
    { year: "2025" },
    { year: "2026" },
  ];

  var wrap = document.createElement("div");
  wrap.className = "mr-badges";
  wrap.setAttribute("aria-label", "The State's Best roofer, winner 2025 and 2026");
  BADGES.forEach(function (b, i) {
    var el = document.createElement("div");
    el.className = "mr-badge mr-badge--" + (i ? "right" : "left");
    el.innerHTML = '<img src="/assets/site/badges/the-states-best-' + b.year + '.png" alt="The State\u2019s Best ' + b.year + ' Winner" width="225" height="231">';
    wrap.appendChild(el);
  });
  var eyebrow = document.createElement("div");
  eyebrow.className = "mr-eyebrow";
  eyebrow.innerHTML = 'Back-to-Back Winner<span class="mr-eyebrow-more"> · The State’s Best</span>';

  var row = h1.closest(".widget-row") || h1.parentNode;
  row.parentNode.insertBefore(eyebrow, row);
  // wide: badges flank the headline (absolute in the hero content); narrow: in flow above the eyebrow
  var gc = hero.querySelector(".grid-content") || hero, mq = window.matchMedia("(min-width: 1100px)");
  function place() {
    if (mq.matches) gc.appendChild(wrap);
    else eyebrow.parentNode.insertBefore(wrap, eyebrow);
  }
  place();
  mq.addEventListener ? mq.addEventListener("change", place) : mq.addListener(place);
  hero.classList.add("mr-hero--home");
})();
