/* Shared GA4 events and Calendly popup for every RAINCLOUD template.
   Events: cta_click, outside_audit_start, outside_audit_request,
   book_call_click, book_call_scheduled, framework_request,
   benchmark_download, contact_form_submit, pricing_cta_click,
   email_click, phone_click.
   Standard events carry page_location, page_template, cta_position,
   cta_id, cluster, persona, offer, cta_label, the first-touch UTMs
   and referrer. email_click and phone_click carry page_location,
   page_template, cta_position, link_url and the same attribution. */
(function () {
  var CALENDLY_CSS = "https://assets.calendly.com/assets/external/widget.css";
  var CALENDLY_JS = "https://assets.calendly.com/assets/external/widget.js";
  var UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"];
  var STORE_KEY = "rc_attribution";
  var OFFERS = {
    "outside-audit": "outside-audit",
    "outside_audit": "outside-audit",
    "gtm-autopsy": "gtm-autopsy",
    "gtm_autopsy": "gtm-autopsy",
    "autopsy": "gtm-autopsy",
    "gtm-fix": "gtm-fix",
    "gtm_fix": "gtm-fix",
    "advisory": "advisory",
    "scorecard": "scorecard",
    "general": "general"
  };
  var pending = null;
  var attribution = blankAttribution("");
  var applying = false;

  function attr(el, name) {
    if (!el || !el.getAttribute) return "";
    return el.getAttribute(name) || "";
  }

  function clip(value, max) {
    var text = value == null ? "" : String(value);
    text = text.replace(/[\u0000-\u001f\u007f]/g, "").replace(/\s+/g, " ").trim();
    if (text.length > max) return text.slice(0, max);
    return text;
  }

  function blankAttribution(referrer) {
    return {
      utm_source: "",
      utm_medium: "",
      utm_campaign: "",
      utm_term: "",
      utm_content: "",
      referrer: referrer || ""
    };
  }

  function hasAnyUtm(record) {
    if (!record) return false;
    for (var i = 0; i < UTM_KEYS.length; i++) {
      if (record[UTM_KEYS[i]]) return true;
    }
    return false;
  }

  function storageGet(store) {
    try {
      return store.getItem(STORE_KEY);
    } catch (e) {
      return null;
    }
  }

  function storageSet(store, record) {
    try {
      store.setItem(STORE_KEY, JSON.stringify(record));
    } catch (e) {}
  }

  function readStore(store) {
    var raw = storageGet(store);
    if (!raw) return null;
    try {
      var data = JSON.parse(raw);
      if (!data || typeof data !== "object") return null;
      var record = blankAttribution(clip(data.referrer || "", 500));
      UTM_KEYS.forEach(function (key) {
        record[key] = clip(data[key] || "", 100);
      });
      return record;
    } catch (e) {
      return null;
    }
  }

  function fromSearch(search) {
    var params;
    try {
      params = new URLSearchParams(search || "");
    } catch (e) {
      return blankAttribution("");
    }
    var record = blankAttribution("");
    UTM_KEYS.forEach(function (key) {
      record[key] = clip(params.get(key) || "", 100);
    });
    return record;
  }

  function captureAttribution() {
    var incoming = fromSearch(window.location.search);
    var stored = readStore(window.localStorage);
    var session = readStore(window.sessionStorage);
    var referrer = clip((session && session.referrer) || document.referrer || "", 500);

    if (hasAnyUtm(incoming)) {
      if (!stored || !hasAnyUtm(stored)) {
        incoming.referrer = referrer;
        storageSet(window.localStorage, incoming);
        storageSet(window.sessionStorage, incoming);
        attribution = incoming;
        return;
      }
    }

    if (stored && hasAnyUtm(stored)) {
      if (!stored.referrer) stored.referrer = referrer;
      storageSet(window.sessionStorage, stored);
      attribution = stored;
      return;
    }

    if (!session) {
      session = blankAttribution(referrer);
      storageSet(window.sessionStorage, session);
    }
    attribution = session;
  }

  function attributionParams() {
    var data = {};
    UTM_KEYS.forEach(function (key) {
      data[key] = attribution[key] || "";
    });
    data.referrer = clip(attribution.referrer || "", 100);
    return data;
  }

  function canonicalOffer(value) {
    var key = clip(value, 40).toLowerCase();
    return OFFERS[key] || "";
  }

  function pathOf(url) {
    if (!url) return "";
    try {
      return new URL(url, window.location.href).pathname.toLowerCase();
    } catch (e) {
      return String(url).split("?")[0].split("#")[0].toLowerCase();
    }
  }

  function offerFromPath(path) {
    var value = path || "";
    if (value.indexOf("outside-audit") !== -1) return "outside-audit";
    if (value.indexOf("gtm-autopsy") !== -1) return "gtm-autopsy";
    if (value.indexOf("gtm-fix") !== -1 || value.indexOf("gtm-consulting") !== -1) return "gtm-fix";
    if (value.indexOf("scorecard") !== -1) return "scorecard";
    if (value.indexOf("advisory") !== -1) return "advisory";
    return "";
  }

  function offerOf(el) {
    var node = el;
    while (node && node.getAttribute) {
      var explicit = canonicalOffer(node.getAttribute("data-offer") || "");
      if (explicit) return explicit;
      node = node.parentElement;
    }
    var fromKind = canonicalOffer(attr(el, "data-track"));
    if (fromKind) return fromKind;
    var href = attr(el, "href") || attr(el, "data-url");
    var fromHref = offerFromPath(pathOf(href));
    if (fromHref) return fromHref;
    var fromPage = offerFromPath(pathOf(window.location.pathname));
    if (fromPage) return fromPage;
    var template = attr(document.body, "data-page-template");
    if (template === "gtm-consulting") return "gtm-fix";
    if (template === "outside-audit") return "outside-audit";
    if (template === "gtm-autopsy") return "gtm-autopsy";
    return "general";
  }

  function submitButton(form) {
    if (!form || !form.querySelector) return null;
    return form.querySelector('button[type="submit"], button:not([type]), input[type="submit"]');
  }

  function labelOf(el) {
    if (!el || !el.tagName) return "";
    var source = el;
    if (el.tagName === "FORM") {
      var button = submitButton(el);
      if (button) {
        var saved = attr(button, "data-rc-label");
        if (saved) return clip(saved, 100);
        source = button;
      }
    }
    return clip(source.textContent || "", 100);
  }

  function rememberLabels() {
    var forms = document.querySelectorAll("form");
    for (var i = 0; i < forms.length; i++) {
      var button = submitButton(forms[i]);
      if (!button || attr(button, "data-rc-label")) continue;
      var label = clip(button.textContent || button.value || "", 100);
      if (label) button.setAttribute("data-rc-label", label);
    }
  }

  function positionOf(el) {
    var explicit = attr(el, "data-cta-position") || attr(el, "data-cta");
    if (explicit) return clip(explicit, 100);
    if (!el || !el.closest) return "";
    if (el.closest("footer")) return "footer";
    if (el.closest("nav")) return "nav";
    if (el.closest(".contact-detail, .contact-info")) return "contact";
    return "";
  }

  function payload(el) {
    var body = document.body;
    var data = {
      page_location: window.location.href,
      page_template: attr(el, "data-page-template") || attr(body, "data-page-template"),
      cta_position: attr(el, "data-cta-position") || attr(el, "data-cta"),
      cta_id: attr(el, "data-cta-id"),
      cluster: attr(el, "data-cluster") || attr(body, "data-cluster"),
      persona: attr(el, "data-persona") || attr(body, "data-persona"),
      offer: offerOf(el),
      cta_label: labelOf(el)
    };
    if (!data.cta_id && el && el.classList && el.classList.contains("calendly-inline-widget")) {
      data.cta_id = "contact-embed";
      if (!data.cta_position) data.cta_position = "embed";
    }
    var utm = attributionParams();
    UTM_KEYS.forEach(function (key) {
      data[key] = utm[key];
    });
    data.referrer = utm.referrer;
    return data;
  }

  function linkPayload(el, linkUrl) {
    var body = document.body;
    var data = {
      page_location: window.location.href,
      page_template: attr(el, "data-page-template") || attr(body, "data-page-template"),
      cta_position: positionOf(el),
      link_url: clip(linkUrl || "", 100)
    };
    var utm = attributionParams();
    UTM_KEYS.forEach(function (key) {
      data[key] = utm[key];
    });
    data.referrer = utm.referrer;
    return data;
  }

  function track(name, el) {
    if (typeof window.gtag !== "function") return;
    var data = payload(el);
    if (name === "pricing_cta_click") {
      data.cta = attr(el, "data-cta");
      data.cta_text = labelOf(el).slice(0, 80);
      data.page = window.location.pathname;
    }
    try {
      window.gtag("event", name, data);
    } catch (e) {}
  }

  function trackLink(name, el, linkUrl) {
    if (typeof window.gtag !== "function") return;
    try {
      window.gtag("event", name, linkPayload(el, linkUrl));
    } catch (e) {}
  }

  window.rcTrack = track;
  window.rcAttribution = function () {
    var copy = blankAttribution(attribution.referrer || "");
    UTM_KEYS.forEach(function (key) {
      copy[key] = attribution[key] || "";
    });
    return copy;
  };

  function mergedCalendly(url) {
    if (!hasAnyUtm(attribution)) return url;
    var parsed;
    try {
      parsed = new URL(url, window.location.href);
    } catch (e) {
      return url;
    }
    if (parsed.hostname.indexOf("calendly.com") === -1) return url;
    var changed = false;
    UTM_KEYS.forEach(function (key) {
      var incoming = attribution[key] || "";
      var current = parsed.searchParams.get(key);
      if (incoming) {
        if (current !== incoming) {
          parsed.searchParams.set(key, incoming);
          changed = true;
        }
      } else if (current !== null) {
        parsed.searchParams.delete(key);
        changed = true;
      }
    });
    return changed ? parsed.toString() : url;
  }

  function applyUtmsToCalendly() {
    if (applying) return;
    applying = true;
    try {
      var links = document.querySelectorAll('a[href*="calendly.com"]');
      for (var i = 0; i < links.length; i++) {
        var href = links[i].href || links[i].getAttribute("href") || "";
        var next = mergedCalendly(href);
        if (next !== href) links[i].setAttribute("href", next);
      }
      var widgets = document.querySelectorAll('[data-url*="calendly.com"]');
      for (var j = 0; j < widgets.length; j++) {
        var raw = widgets[j].getAttribute("data-url") || "";
        var merged = mergedCalendly(raw);
        if (merged !== raw) widgets[j].setAttribute("data-url", merged);
        var frame = widgets[j].querySelector("iframe");
        if (frame && frame.src && frame.src.indexOf("calendly.com") !== -1) {
          var frameNext = mergedCalendly(frame.src);
          if (frameNext !== frame.src) frame.src = frameNext;
        }
      }
    } finally {
      applying = false;
    }
  }

  function stampContactForm() {
    var form = document.getElementById("contactForm");
    if (!form) return;
    UTM_KEYS.concat(["referrer"]).forEach(function (name) {
      var input = form.querySelector('input[type="hidden"][name="' + name + '"]');
      if (!input) {
        input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.setAttribute("data-rc-utm", "1");
        form.appendChild(input);
      }
      input.value = name === "referrer" ? (attribution.referrer || "") : (attribution[name] || "");
    });
  }

  function loadWidget(done, fail) {
    if (window.Calendly && window.Calendly.initPopupWidget) {
      done();
      return;
    }
    if (!document.querySelector("link[data-rc-calendly]")) {
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = CALENDLY_CSS;
      link.setAttribute("data-rc-calendly", "1");
      document.head.appendChild(link);
    }
    var existing = document.querySelector("script[data-rc-calendly]");
    if (existing) {
      existing.addEventListener("load", done);
      existing.addEventListener("error", fail);
      return;
    }
    var script = document.createElement("script");
    script.src = CALENDLY_JS;
    script.async = true;
    script.setAttribute("data-rc-calendly", "1");
    script.addEventListener("load", done);
    script.addEventListener("error", fail);
    document.head.appendChild(script);
  }

  function openCalendly(anchor) {
    var url = mergedCalendly(anchor.href);
    if (url !== anchor.href) anchor.setAttribute("href", url);
    loadWidget(
      function () {
        if (window.Calendly && window.Calendly.initPopupWidget) {
          window.Calendly.initPopupWidget({ url: url });
        } else {
          window.location.href = url;
        }
      },
      function () {
        window.location.href = url;
      }
    );
  }

  function kindOf(anchor, href) {
    var kind = attr(anchor, "data-track");
    if (kind) return kind;
    if (href.indexOf("calendly.com") !== -1) return "book_call";
    return "";
  }

  function onPricingPage() {
    if (attr(document.body, "data-page-template") === "pricing") return true;
    return (window.location.pathname || "").indexOf("/pricing") === 0;
  }

  function clickTarget(event) {
    var target = event.target;
    if (!target) return null;
    if (target.nodeType !== 1) target = target.parentElement;
    if (!target || !target.closest) return null;
    return target.closest("a[href], button[data-track]");
  }

  document.addEventListener("click", function (event) {
    var anchor = clickTarget(event);
    if (!anchor) return;
    var href = anchor.getAttribute("href") || "";
    var lower = href.toLowerCase();

    if (lower.indexOf("mailto:") === 0) {
      trackLink("email_click", anchor, href);
      return;
    }
    if (lower.indexOf("tel:") === 0) {
      trackLink("phone_click", anchor, href);
      return;
    }

    if (onPricingPage()) {
      var priced = anchor.closest("[data-cta]");
      if (priced) track("pricing_cta_click", priced);
    }

    var kind = kindOf(anchor, href);
    if (!kind && href.indexOf("calendly.com") === -1) return;

    if (kind === "framework") {
      track("cta_click", anchor);
      track("framework_request", anchor);
      return;
    }
    if (kind === "benchmark") {
      track("cta_click", anchor);
      track("benchmark_download", anchor);
      return;
    }
    if (href.indexOf("calendly.com") === -1) {
      if (kind) track("cta_click", anchor);
      return;
    }

    track("cta_click", anchor);
    if (kind === "outside_audit") {
      track("outside_audit_start", anchor);
      pending = { kind: "outside_audit", el: anchor };
    } else {
      track("book_call_click", anchor);
      pending = { kind: "book_call", el: anchor };
    }
    event.preventDefault();
    openCalendly(anchor);
  }, true);

  window.addEventListener("message", function (event) {
    if (!event.origin || event.origin.indexOf("calendly.com") === -1) return;
    var data = event.data;
    if (typeof data === "string") {
      try {
        data = JSON.parse(data);
      } catch (e) {
        return;
      }
    }
    if (!data || data.event !== "calendly.event_scheduled") return;
    if (pending && pending.kind === "outside_audit") {
      track("outside_audit_request", pending.el);
    } else if (pending) {
      track("book_call_scheduled", pending.el);
    } else {
      track("book_call_scheduled", document.querySelector(".calendly-inline-widget") || document.body);
    }
    pending = null;
  });

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (form && form.id === "contactForm") stampContactForm();
  }, true);

  function start() {
    captureAttribution();
    rememberLabels();
    applyUtmsToCalendly();
    stampContactForm();
    if (window.MutationObserver && document.body) {
      var observer = new MutationObserver(function () {
        applyUtmsToCalendly();
      });
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["src", "data-url"]
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
