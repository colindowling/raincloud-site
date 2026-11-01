/* Shared header behavior. Desktop menus open on hover and on keyboard
   focus. Below 1024px the hamburger opens one panel and each group toggles
   on click, so the first tap never navigates away. */
(function () {
  if (window.__rcNav) return;
  window.__rcNav = true;

  var DESKTOP = window.matchMedia("(min-width: 1024px)");

  function ready() {
    var nav = document.getElementById("nav");
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (!nav || !toggle || !links) return;

    var drops = Array.prototype.slice.call(nav.querySelectorAll(".has-dropdown"));
    var blockFocusOpen = false;

    function desktop() {
      return DESKTOP.matches;
    }

    function setExpanded(drop, open) {
      var button = drop.querySelector(".nav-parent");
      if (button) button.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function closeDrop(drop) {
      drop.classList.remove("is-open");
      drop.classList.remove("is-hover");
      drop.classList.add("is-dismissed");
      setExpanded(drop, false);
    }

    function dismissAndFocus(drop) {
      var button = drop.querySelector(".nav-parent");
      blockFocusOpen = true;
      closeDrop(drop);
      if (button) button.focus();
      blockFocusOpen = false;
    }

    function closeDrops(except) {
      drops.forEach(function (drop) {
        if (drop === except) return;
        drop.classList.remove("is-open");
        drop.classList.remove("is-hover");
        drop.classList.remove("is-dismissed");
        setExpanded(drop, false);
      });
    }

    function setMenu(open) {
      links.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (!open) closeDrops(null);
    }

    function align(drop) {
      var menu = drop.querySelector(".dropdown");
      if (!menu) return;
      if (!desktop()) {
        menu.classList.remove("is-end");
        return;
      }
      menu.classList.remove("is-end");
      var rect = menu.getBoundingClientRect();
      if (rect.width === 0) return;
      if (rect.right > window.innerWidth - 8) {
        menu.classList.add("is-end");
        rect = menu.getBoundingClientRect();
      }
      if (rect.left < 8) menu.classList.remove("is-end");
    }

    function alignAll() {
      drops.forEach(align);
    }

    document.addEventListener(
      "click",
      function (event) {
        var hit = event.target.closest && event.target.closest("#navToggle");
        if (!hit || hit !== toggle) return;
        event.preventDefault();
        event.stopPropagation();
        setMenu(!links.classList.contains("open"));
      },
      true
    );

    drops.forEach(function (drop) {
      var button = drop.querySelector(".nav-parent");
      if (!button) return;

      drop.addEventListener("pointerenter", function (event) {
        if (!desktop() || event.pointerType === "touch") return;
        drop.classList.remove("is-dismissed");
        drop.classList.add("is-hover");
        setExpanded(drop, true);
        align(drop);
        if (!drop.classList.contains("is-open")) {
          drop.dataset.suppressClick = "1";
          window.setTimeout(function () {
            drop.dataset.suppressClick = "";
          }, 450);
        }
      });

      drop.addEventListener("mouseleave", function () {
        if (!desktop()) return;
        drop.classList.remove("is-hover");
        drop.classList.remove("is-dismissed");
        if (!drop.classList.contains("is-open") && !drop.contains(document.activeElement)) {
          setExpanded(drop, false);
        }
      });

      drop.addEventListener("focusin", function () {
        if (!desktop() || blockFocusOpen) return;
        drop.classList.remove("is-dismissed");
        setExpanded(drop, true);
        align(drop);
      });

      drop.addEventListener("focusout", function (event) {
        if (drop.contains(event.relatedTarget)) return;
        if (!drop.classList.contains("is-open")) setExpanded(drop, false);
      });

      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (!desktop()) {
          var willOpen = !drop.classList.contains("is-open");
          closeDrops(drop);
          drop.classList.toggle("is-open", willOpen);
          setExpanded(drop, willOpen);
          return;
        }
        if (drop.dataset.suppressClick === "1") {
          drop.dataset.suppressClick = "";
          setExpanded(drop, true);
          return;
        }
        var willOpenDesktop = !drop.classList.contains("is-open");
        closeDrops(drop);
        drop.classList.toggle("is-open", willOpenDesktop);
        if (willOpenDesktop) drop.classList.remove("is-dismissed");
        else drop.classList.add("is-dismissed");
        setExpanded(drop, willOpenDesktop || drop.classList.contains("is-hover"));
        align(drop);
      });

      drop.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        var open = drop.classList.contains("is-open") || drop.classList.contains("is-hover") || button.getAttribute("aria-expanded") === "true";
        if (!open) return;
        event.preventDefault();
        event.stopPropagation();
        dismissAndFocus(drop);
      });
    });

    links.addEventListener("click", function (event) {
      var anchor = event.target.closest && event.target.closest("a");
      if (!anchor || !links.contains(anchor)) return;
      if (!desktop()) setMenu(false);
    });

    document.addEventListener("click", function (event) {
      if (nav.contains(event.target)) return;
      closeDrops(null);
      if (links.classList.contains("open")) setMenu(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      var openDrop = null;
      drops.forEach(function (drop) {
        var button = drop.querySelector(".nav-parent");
        if (drop.classList.contains("is-open") || (button && button.getAttribute("aria-expanded") === "true")) {
          openDrop = drop;
        }
      });
      if (openDrop) {
        dismissAndFocus(openDrop);
        return;
      }
      if (links.classList.contains("open")) {
        setMenu(false);
        toggle.focus();
      }
    });

    function onViewportChange() {
      if (desktop()) setMenu(false);
      alignAll();
    }

    if (DESKTOP.addEventListener) DESKTOP.addEventListener("change", onViewportChange);
    else if (DESKTOP.addListener) DESKTOP.addListener(onViewportChange);
    window.addEventListener("resize", alignAll);
    alignAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();
