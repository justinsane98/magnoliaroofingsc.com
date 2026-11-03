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
    var h = mh && mh.offsetParent !== null ? mh.offsetHeight : 0;
    document.documentElement.style.setProperty("--mr-header-h", h + "px");
  }
  syncHeader();
  window.addEventListener("resize", syncHeader);
  window.addEventListener("load", syncHeader); // logo image may change the header height once loaded

  /* ---------- Language switcher: minimal "EN | ES" in the header ---------- */
  // GTranslate's ln.js (loaded deferred, after this script) fills every .mr-lang with language links.
  (function () {
    var chat = document.getElementById("header-widget-1761842589315");
    if (chat) {
      var d = document.createElement("div");
      d.className = "mr-lang mr-lang--desktop notranslate";
      chat.parentNode.insertBefore(d, chat);
    }
    var bar = document.querySelector(".mobile-menu.is-absolute");
    if (bar) {
      var m = document.createElement("div");
      m.className = "mr-lang mr-lang--mobile notranslate";
      bar.appendChild(m);
    }
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
      '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0 0 22 12z"/></svg></a>' +
      "<span>Copyright © " + new Date().getFullYear() + ". Magnolia Roofing &amp; Remodeling LLC. All Rights Reserved.</span>" +
      '<a href="javascript:WebPlatform.Popups.show(1);">Privacy Policy</a>';
    col.appendChild(line);
  })();

  /* ---------- Contact form ---------- */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function submitForm(form, btn) {
    var fields = form.querySelectorAll(".form-field");
    var data = {}, ok = true;
    fields.forEach(function (f) {
      var el = f.querySelector("input, textarea, select");
      if (!el) return;
      var name = el.getAttribute("data-name") || el.name, val = (el.value || "").trim();
      var type = el.getAttribute("data-type");
      var bad = !val || (type === "email" && !EMAIL_RE.test(val));
      f.classList.toggle("field-invalid", bad);
      if (bad) ok = false;
      data[name] = val;
    });
    if (!ok) return;

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

  /* ---------- "CHAT NOW!" button: text on mobile, contact form on desktop ---------- */
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
    box.style.cssText = "background:#fff;color:#222;max-width:760px;width:100%;max-height:85vh;overflow:auto;border-radius:8px;padding:32px;position:relative;font-family:Manrope,sans-serif;line-height:1.6";
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
})();
