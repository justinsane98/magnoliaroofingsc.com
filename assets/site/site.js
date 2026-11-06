// Replaces GoSite-hosted features (form handler, chat, privacy popup) with free/static ones.
(function () {
  var C = window.SITE_CONFIG || {};

  /* ---------- Email delivery (FormSubmit by default, Web3Forms if a key is set) ---------- */
  function sendEmail(subject, data) {
    var url, body;
    if (C.web3formsKey) {
      url = "https://api.web3forms.com/submit";
      body = Object.assign({ access_key: C.web3formsKey, subject: subject, from_name: "magnoliaroofingsc.com" }, data);
    } else {
      url = "https://formsubmit.co/ajax/" + encodeURIComponent(C.formEmail);
      body = Object.assign({ _subject: subject, _template: "table", _captcha: "false" }, data);
      if (data.Email) body._replyto = data.Email;
    }
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }
  window.SiteEmail = sendEmail; // used by reviews.js

  /* ---------- Mobile header overlap ---------- */
  // On mobile/tablet the logo header is absolutely positioned over the first section (hero).
  // Measure it and expose the height so site.css can pad the hero content below it.
  var firstRow = document.querySelector(".content .grid-row");
  if (firstRow) firstRow.classList.add("mr-hero");
  function syncHeader() {
    var mh = document.querySelector(".mobile-menu.is-absolute");
    var h = mh && getComputedStyle(mh).display !== "none" ? mh.getBoundingClientRect().height : 0; // (fixed elements have no offsetParent)
    document.documentElement.style.setProperty("--mr-header-h", h + "px");
  }
  syncHeader();
  window.addEventListener("resize", syncHeader);
  window.addEventListener("load", syncHeader); // logo image may change the header height once loaded

  /* ---------- Sticky header: pin + shrink after a little scroll ---------- */
  (function () {
    var wrap = document.querySelector(".main-header-wrapper"), row = document.querySelector(".header-row-main");
    if (wrap && row) {
      // slide the bar flush to the top edge when pinned
      var gap = row.getBoundingClientRect().top - wrap.getBoundingClientRect().top;
      document.documentElement.style.setProperty("--mr-stuck-top", -Math.max(0, gap) + "px");
    }
    var stuck = null;
    function onScroll() {
      var s = window.scrollY > 40;
      if (s !== stuck) { stuck = s; document.documentElement.classList.toggle("mr-stuck", s); }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  })();

  /* ---------- Rounded containers ---------- */
  // Round the outer corners of each content "card" (one or more side-by-side columns with a
  // background). Full-width (edge-to-edge) sections stay square.
  function roundCards() {
    var vw = document.documentElement.clientWidth;
    document.querySelectorAll(".content .grid-content").forEach(function (gc) {
      var cols = [].filter.call(gc.children, function (c) {
        if (!c.classList.contains("grid-column") || !c.offsetHeight) return false;
        var cs = getComputedStyle(c);
        // white with content flush to a side edge is page, not a box - e.g. "Connect With Us"
        if (cs.backgroundColor === "rgb(255, 255, 255)" && cs.backgroundImage === "none" &&
            (!parseFloat(cs.paddingLeft) || !parseFloat(cs.paddingRight))) return false;
        return cs.backgroundColor !== "rgba(0, 0, 0, 0)" || cs.backgroundImage !== "none";
      });
      cols.forEach(function (c) { c.classList.remove("mr-round-l", "mr-round-r", "mr-round-t", "mr-round-b", "mr-card-row"); });
      gc.classList.remove("mr-card-row");
      if (!cols.length) return;
      var rs = cols.map(function (c) { return c.getBoundingClientRect(); });
      var left = Math.min.apply(null, rs.map(function (r) { return r.left; }));
      var right = Math.max.apply(null, rs.map(function (r) { return r.right; }));
      if (right - left >= vw * 0.97) return; // edge-to-edge band
      // Floating card: gets the shared lift shadow (site.css). A lone card column is shadowed on its
      // own, so content painted beside it in the same row (e.g. "Connect With Us") casts nothing.
      (cols.length === 1 ? cols[0] : gc).classList.add("mr-card-row");
      var stacked = rs.length > 1 && Math.abs(rs[0].left - rs[1].left) < 2;
      if (cols.length === 1) { cols[0].classList.add("mr-round-l", "mr-round-r"); return; }
      cols[0].classList.add(stacked ? "mr-round-t" : "mr-round-l");
      cols[cols.length - 1].classList.add(stacked ? "mr-round-b" : "mr-round-r");
    });
  }
  roundCards();
  window.addEventListener("load", roundCards);
  window.addEventListener("resize", roundCards);

  /* ---------- Header CTAs: phone number (primary) + Chat (secondary) ---------- */
  ["header-widget-1761842589315", "header-widget-1761842589315-mobile"].forEach(function (id) {
    var w = document.getElementById(id), chat = w && w.querySelector(".gs-chat-btn");
    if (!chat || w.querySelector(".mr-phone-cta")) return; // phone button is in the HTML now (no layout shift); this is a fallback
    var phone = chat.cloneNode(true);
    phone.className = "button-style js-button button-style-custom mr-phone-cta";
    phone.removeAttribute("data-chat");
    phone.href = "tel:" + (C.phone || "+18039087131");
    phone.textContent = "(803) 908-7131";
    chat.classList.add("mr-chat-secondary");
    chat.parentNode.insertBefore(phone, chat.nextSibling); // primary always on the right
    chat.parentNode.classList.add("mr-header-ctas");
  });

  /* ---------- Mobile/tablet top bar: phone CTA top right ---------- */
  (function () {
    var bar = document.querySelector(".mobile-menu.is-absolute");
    if (!bar) return;
    if (getComputedStyle(bar).position === "static") bar.style.position = "relative";
    var a = document.createElement("a");
    a.className = "mr-bar-call";
    a.href = "tel:" + (C.phone || "+18039087131");
    a.setAttribute("aria-label", "Call (803) 908-7131");
    a.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg><span>(803) 908-7131</span>';
    bar.appendChild(a);
  })();

  /* ---------- Hero CTAs: secondary (chat) left, primary (phone) right ---------- */
  (function () {
    var hero = document.querySelector(".mr-hero");
    var phone = hero && hero.querySelector("a.theme-button.mr-phone-cta"), chat = hero && hero.querySelector("a.theme-button.gs-chat-btn");
    if (!phone || !chat) return;
    if (!(phone.compareDocumentPosition(chat) & Node.DOCUMENT_POSITION_PRECEDING)) {
      var ph = document.createComment("p"), ch = document.createComment("c");
      phone.replaceWith(ph); chat.replaceWith(ch);
      ph.replaceWith(chat); ch.replaceWith(phone);
    }
    // keep the pair on one row on phones too (primary stays on the right)
    var a = chat.closest(".widget"), b = phone.closest(".widget"), row = a;
    while (row && !row.contains(b)) row = row.parentElement;
    if (row) row.classList.add("mr-hero-ctas");
  })();

  /* ---------- Header priority when space runs out ---------- */
  // Drop the MESSAGE button when space runs out; the phone CTA always stays. (Language picker lives in the footer.)
  (function () {
    var root = document.documentElement, flex = document.querySelector(".header-row-main .flex-header");
    if (!flex) return;
    function fits() {
      if (!flex.offsetParent) return true; // desktop header hidden (phone layout)
      if (flex.scrollWidth > flex.clientWidth + 1) return false;
      var lis = flex.querySelectorAll("nav li"), tops = {};
      [].forEach.call(lis, function (li) { if (li.offsetParent) tops[li.offsetTop] = 1; });
      return Object.keys(tops).length <= 1; // nav on one line
    }
    function fit() {
      root.classList.remove("mr-hide-flag", "mr-hide-msg");
      if (!fits()) root.classList.add("mr-hide-flag");
      if (!fits()) root.classList.add("mr-hide-msg");
    }
    var t;
    function later() { clearTimeout(t); t = setTimeout(fit, 400); } // after the pin/shrink transition
    window.addEventListener("resize", fit);
    window.addEventListener("load", fit);
    window.addEventListener("scroll", later, { passive: true });
    setTimeout(fit, 0);
  })();

  /* ---------- Language switcher: flag tab hanging off the bottom of the header ---------- */
  // GTranslate's ln.js (deferred, runs after this) renders its language links into the hidden .mr-lang;
  // the flag tab + dropdown just clicks those links.
  (function () {
    var LANGS = [
      { code: "en", name: "English", flag: "/assets/site/flags/en-us.svg" },
      { code: "es", name: "Español", flag: "/assets/site/flags/es-mx.svg" },
    ];
    var engine = document.createElement("div");
    engine.className = "mr-lang notranslate";
    engine.hidden = true;
    document.body.appendChild(engine);

    function currentLang() {
      var a = engine.querySelector("a.gt-current-lang");
      if (a) return a.getAttribute("data-gt-lang");
      var m = document.cookie.match(/googtrans=\/[a-z-]+\/([a-z-]+)/);
      return m ? m[1] : "en";
    }
    function langInfo(code) { return LANGS.filter(function (l) { return l.code === code; })[0] || LANGS[0]; }

    var tabs = [];
    function makeTab(host, cls) {
      if (!host) return;
      if (getComputedStyle(host).position === "static") host.style.position = "relative";
      var tab = document.createElement("div");
      tab.className = "mr-flag-tab notranslate " + cls;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "mr-flag-btn";
      btn.setAttribute("aria-haspopup", "listbox");
      btn.setAttribute("aria-expanded", "false");
      btn.innerHTML = '<img alt="" width="28" height="21"><span class="mr-flag-caret" aria-hidden="true"></span>';
      var menu = document.createElement("ul");
      menu.className = "mr-flag-menu";
      menu.setAttribute("role", "listbox");
      menu.hidden = true;
      LANGS.forEach(function (l) {
        var li = document.createElement("li");
        li.setAttribute("role", "option");
        li.dataset.lang = l.code;
        li.tabIndex = 0;
        li.innerHTML = '<img alt="" width="24" height="18" src="' + l.flag + '"><span>' + l.name + "</span>";
        function pick() {
          var link = engine.querySelector('a[data-gt-lang="' + l.code + '"]');
          if (link) link.click();
          close();
          setTimeout(paintAll, 50);
        }
        li.addEventListener("click", pick);
        li.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
        menu.appendChild(li);
      });
      function close() { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); }
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = menu.hidden;
        tabs.forEach(function (t) { t.close(); });
        menu.hidden = !open;
        btn.setAttribute("aria-expanded", String(open));
      });
      tab.appendChild(btn);
      tab.appendChild(menu);
      host.appendChild(tab);
      tabs.push({ btn: btn, menu: menu, close: close });
    }
    function paintAll() {
      var cur = langInfo(currentLang());
      tabs.forEach(function (t) {
        var img = t.btn.querySelector("img");
        img.src = cur.flag;
        t.btn.setAttribute("aria-label", "Language: " + cur.name);
        [].forEach.call(t.menu.children, function (li) { li.setAttribute("aria-selected", String(li.dataset.lang === cur.code)); });
      });
    }

    // desktop: in the footer line, right of the Facebook icon (the footer script moves it there)
    var ctas = document.querySelector("#header-widget-1761842589315 .mr-header-ctas");
    makeTab(ctas, "mr-flag-tab--desktop");
    // mobile/tablet: last item in the slide-out menu, side by side with the Facebook icon
    var drawer = document.querySelector(".mobile-header-wrapper");
    if (drawer) {
      var row = document.createElement("div");
      row.className = "mr-drawer-social";
      row.innerHTML = '<a class="mr-drawer-fb" href="https://www.facebook.com/magnoliaroofingsc/" target="_blank" rel="noopener" aria-label="Magnolia Roofing on Facebook">' +
        '<svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true"><path fill="currentColor" d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0 0 22 12z"/></svg></a>';
      drawer.appendChild(row);
      makeTab(row, "mr-flag-tab--drawer");
    }
    paintAll();
    window.addEventListener("load", paintAll); // ln.js has marked the current language by now
    document.addEventListener("click", function () { tabs.forEach(function (t) { t.close(); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") tabs.forEach(function (t) { t.close(); }); });
  })();

  /* ---------- Footer: one left-aligned line (Facebook icon · copyright · privacy) ---------- */
  (function () {
    var cp = [].find.call(document.querySelectorAll(".text-widget-content"), function (e) {
      return /Copyright\s*©/.test(e.textContent);
    });
    if (!cp) return;
    var col = cp.closest(".grid-column");
    if (!col) return;
    // hide the old rows (social icon pill, copyright, privacy link, hidden GoSite badge)
    [].forEach.call(col.querySelectorAll(":scope > .widget-row"), function (r) { r.style.display = "none"; });

    var line = document.createElement("div");
    line.className = "mr-footer-line";
    line.innerHTML =
      '<a class="mr-footer-fb" href="https://www.facebook.com/magnoliaroofingsc/" target="_blank" rel="noopener" aria-label="Magnolia Roofing on Facebook">' +
      '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0 0 22 12z"/></svg></a>' +
      "<span>Copyright © " + new Date().getFullYear() + ". Magnolia Roofing &amp; Remodeling LLC. All Rights Reserved.</span>" +
      '<a href="javascript:WebPlatform.Popups.show(1);">Privacy Policy</a>';
    col.appendChild(line);
    var flag = document.querySelector(".mr-flag-tab--desktop");
    if (flag) line.appendChild(flag); // language picker sits right of the Facebook icon (desktop)
  })();

  /* ---------- Contact form ---------- */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function submitForm(form, btn) {
    var fields = form.querySelectorAll(".form-field");
    var data = {}, ok = true;
    fields.forEach(function (f) {
      // Only real fields: skip the hidden reCAPTCHA response (no data-name) and intl-tel-input's hidden phone copy.
      var el = f.querySelector("[data-name]:not(.phone-input-hidden)");
      if (!el) return;
      var name = el.getAttribute("data-name") || el.name, val = (el.value || "").trim();
      var type = el.getAttribute("data-type");
      var bad = !val || (type === "email" && !EMAIL_RE.test(val));
      f.classList.toggle("field-invalid", bad);
      if (bad) ok = false;
      data[name] = val;
    });
    if (!ok) {
      var first = form.querySelector(".form-field.field-invalid [data-name]:not(.phone-input-hidden)");
      if (first) first.focus();
      return;
    }

    var label = btn.textContent;
    btn.textContent = "SENDING…";
    btn.style.pointerEvents = "none";

    sendEmail("Website inquiry: " + (data.Subject || ""), data)
      .then(function () {
        form.querySelector(".widget-form-inner-wrapper").innerHTML =
          '<p style="color:#fff;font-family:Manrope,sans-serif;font-size:18px;padding:20px 0">' +
          "Thank you! Your message has been sent. We'll be in touch shortly.</p>";
      })
      .catch(function () {
        btn.textContent = label;
        btn.style.pointerEvents = "";
        alert("Sorry, something went wrong sending your message. Please call us at (803) 908-7131.");
      });
  }

  // Capture phase so the GoSite platform script never sees the submit click.
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest('[data-role="form"] [data-role="submit"]');
    if (!btn) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    submitForm(btn.closest('[data-role="form"]'), btn);
  }, true);

  // Example placeholders, keyed by the field's data-name.
  var PLACEHOLDERS = {
    Name: "John Hasaleak",
    Email: "john@hasaleakinhisroof.com",
    Phone: "(803) 865-5309",
    Subject: "Leak in roof",
    Message: "Wanted to get an estimate and see when you guys could come out and take a look.",
  };
  function applyPlaceholders() {
    document.querySelectorAll('[data-role="form"] [data-name]').forEach(function (el) {
      var p = PLACEHOLDERS[el.getAttribute("data-name")];
      if (p && el.placeholder !== p) el.placeholder = p;
    });
  }
  applyPlaceholders();
  // The platform's phone plugin (intl-tel-input) sets its own "(201) 555-0123" placeholder after load; keep ours.
  new MutationObserver(applyPlaceholders).observe(document.body, { subtree: true, attributes: true, attributeFilter: ["placeholder"] });

  document.addEventListener("input", function (e) {
    var f = e.target.closest && e.target.closest(".form-field.field-invalid");
    if (f) f.classList.remove("field-invalid");
  }, true);

  /* ---------- "MESSAGE" button: text on mobile, contact form on desktop ---------- */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".gs-chat-btn, [data-chat='true']");
    if (!btn) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    if (/Mobi|Android|iPhone/i.test(navigator.userAgent) && C.phone) return (location.href = "sms:" + C.phone);
    location.href = "/#contact";
  }, true);

  /* ---------- Privacy policy popup (was loaded from GoSite API) ---------- */
  var PRIVACY = [
    ["h2", "Privacy Policy"],
    ["h4", "Privacy Commitment"],
    ["p", "We value your privacy. End-user information will not be shared with third parties or affiliates for marketing or promotional purposes. Your information is used solely for the purposes outlined below."],
    ["h4", "Messaging Consent"],
    ["p", "You agree for Magnolia Roofing & Remodeling, LLC to contact you via SMS for various purposes, including but not limited to appointments, communications, billing, and marketing. The frequency of messages may vary depending on the type of communication."],
    ["h4", "Opt-Out Policy"],
    ["p", 'You can cancel the SMS service at any time. Simply text "STOP" to the number that sent you the message. After sending "STOP," you will receive a confirmation SMS that you have been unsubscribed. Once unsubscribed, you will no longer receive SMS messages from us. If you wish to rejoin the SMS service, you can do so by signing up as you did initially.'],
    ["h4", "Support"],
    ["p", 'If you are experiencing issues with the messaging program, reply with the keyword "HELP" for assistance, or contact us directly at magnoliaroofingsc@gmail.com or (803) 908-7131.'],
    ["h4", "Carrier and Cost Disclosures"],
    ["p", "Carriers are not liable for delayed or undelivered messages. Message and data rates may apply for any messages sent to or received from us. For questions about your text or data plan, please contact your wireless provider."],
    ["h4", "Additional Notes"],
    ["p", "We are committed to ensuring that your interactions with us are both secure and respectful of your privacy. If you have any concerns about how your information is handled, please reach out to us at magnoliaroofingsc@gmail.com."],
  ];

  function showPrivacy() {
    var ov = document.createElement("div");
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    ov.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:16px";
    var box = document.createElement("div");
    box.style.cssText = "background:#fff;color:#222;max-width:760px;width:100%;max-height:85vh;overflow:auto;border-radius:var(--mr-r,10px);padding:32px;position:relative;font-family:Manrope,sans-serif;line-height:1.6";
    var x = document.createElement("button");
    x.textContent = "✕";
    x.setAttribute("aria-label", "Close");
    x.style.cssText = "position:absolute;top:10px;right:14px;border:0;background:none;font-size:22px;cursor:pointer";
    box.appendChild(x);
    PRIVACY.forEach(function (b) {
      var el = document.createElement(b[0]);
      el.textContent = b[1];
      el.style.margin = b[0] === "p" ? "0 0 14px" : "18px 0 6px";
      box.appendChild(el);
    });
    ov.appendChild(box);
    function close() { ov.remove(); document.removeEventListener("keydown", esc); }
    function esc(e) { if (e.key === "Escape") close(); }
    ov.addEventListener("click", function (e) { if (e.target === ov || e.target === x) close(); });
    document.addEventListener("keydown", esc);
    document.body.appendChild(ov);
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href*="Popups.show"]');
    if (!a) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    showPrivacy();
  }, true);
  /* ---------- Mobile/tablet menu: full-screen takeover (replaces GoSite's push drawer) ---------- */
  (function () {
    var burger = document.querySelector(".mobile-burger");
    if (!burger) return;
    var logo = document.querySelector(".mobile-menu-logo img");
    var tel = "tel:" + (C.phone || "+18039087131");
    var links = [].map.call(document.querySelectorAll(".header-row-main nav a.website-nav-link"), function (a) {
      var on = a.closest("li").classList.contains("active");
      return '<a class="mr-menu-link' + (on ? " is-active" : "") + '" href="' + a.getAttribute("href") + '"' + (on ? ' aria-current="page"' : "") + ">" + a.textContent.trim() + "</a>";
    }).join("");
    var m = document.createElement("div");
    m.className = "mr-menu";
    m.id = "mr-menu";
    m.setAttribute("role", "dialog");
    m.setAttribute("aria-modal", "true");
    m.setAttribute("aria-label", "Menu");
    m.innerHTML =
      '<div class="mr-menu-top"><a href="/" class="mr-menu-logo" aria-label="Magnolia Roofing home">' + (logo ? '<img src="' + logo.getAttribute("src") + '" alt="">' : "") + "</a>" +
      '<button type="button" class="mr-menu-close" aria-label="Close menu"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></button></div>' +
      '<nav class="mr-menu-body" aria-label="Main">' + links +
      '<div class="mr-menu-ctas">' +
      '<a href="#chat" data-chat="true" class="gs-chat-btn mr-menu-btn mr-menu-btn--sec"><span class="mr-msg-long">SEND A MESSAGE</span><span class="mr-msg-short">MESSAGE</span></a>' +
      '<a href="' + tel + '" class="mr-menu-btn mr-menu-btn--pri">(803) 908-7131</a></div></nav>' +
      '<div class="mr-menu-foot"></div>';
    document.body.appendChild(m);
    var closeBtn = m.querySelector(".mr-menu-close");
    burger.setAttribute("aria-controls", "mr-menu");
    burger.setAttribute("aria-expanded", "false");
    burger.setAttribute("aria-label", "Open menu");
    burger.setAttribute("role", "button");
    burger.tabIndex = 0;

    function open(byKey) {
      var social = document.querySelector(".mr-drawer-social"); // built by the language block
      if (social && social.parentNode !== m.lastChild) m.lastChild.appendChild(social);
      document.documentElement.classList.add("mr-menu-open");
      m.classList.add("is-open");
      burger.setAttribute("aria-expanded", "true");
      if (byKey) setTimeout(function () { closeBtn.focus(); }, 50); // no focus ring after a tap
    }
    function close(refocus) {
      if (!m.classList.contains("is-open")) return;
      document.documentElement.classList.remove("mr-menu-open");
      m.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
      if (refocus) burger.focus();
    }
    // capture on window so GoSite's own burger handler never runs
    ["click", "touchend"].forEach(function (ev) {
      window.addEventListener(ev, function (e) {
        if (!e.target.closest || !e.target.closest(".mobile-burger")) return;
        e.preventDefault(); e.stopImmediatePropagation();
        open(); // touchend's preventDefault cancels the click on phones, so open on either
      }, true);
    });
    burger.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(true); } });
    closeBtn.addEventListener("click", function () { close(true); });
    // any link/button in the menu closes it (window capture: runs before the MESSAGE handler stops the event)
    window.addEventListener("click", function (e) {
      if (e.target.closest && e.target.closest(".mr-menu a") && !e.target.closest(".mr-flag-tab--drawer")) close(false);
    }, true);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(true); });
    window.addEventListener("resize", function () { if (window.innerWidth > 1024) close(false); });
  })();
})();
