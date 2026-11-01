/* Shared GA4 events and Calendly popup for every RAINCLOUD template.
   Events: cta_click, outside_audit_start, outside_audit_request,
   book_call_click, book_call_scheduled, framework_request,
   benchmark_download, contact_form_submit.
   Each event carries page_location, page_template, cta_position,
   cta_id, cluster and persona from data attributes. */
(function () {
  var CALENDLY_CSS = "https://assets.calendly.com/assets/external/widget.css";
  var CALENDLY_JS = "https://assets.calendly.com/assets/external/widget.js";
  var pending = null;

  function attr(el, name) {
    if (!el || !el.getAttribute) return "";
    return el.getAttribute(name) || "";
  }

  function payload(el) {
    var body = document.body;
    return {
      page_location: window.location.href,
      page_template: attr(el, "data-page-template") || attr(body, "data-page-template"),
      cta_position: attr(el, "data-cta-position") || attr(el, "data-cta"),
      cta_id: attr(el, "data-cta-id"),
      cluster: attr(el, "data-cluster") || attr(body, "data-cluster"),
      persona: attr(el, "data-persona") || attr(body, "data-persona")
    };
  }

  function track(name, el) {
    if (typeof window.gtag !== "function") return;
    window.gtag("event", name, payload(el));
  }

  window.rcTrack = track;

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
    var url = anchor.href;
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

  document.addEventListener("click", function (event) {
    var anchor = event.target.closest("a[href], button[data-track]");
    if (!anchor) return;
    var href = anchor.getAttribute("href") || "";
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
    var data = event.data;
    if (!data || data.event !== "calendly.event_scheduled") return;
    if (event.origin && event.origin.indexOf("calendly.com") === -1) return;
    if (pending && pending.kind === "outside_audit") {
      track("outside_audit_request", pending.el);
    } else {
      track("book_call_scheduled", pending ? pending.el : document.body);
    }
    pending = null;
  });
})();
