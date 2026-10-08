(function () {
  var ORDER = { login: 0, reset: 1, register: 2 };
  var SLIDE_MS = 320;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function kindFromUrl(href) {
    if (!href) return "";
    if (href.indexOf("registration") !== -1) return "register";
    if (href.indexOf("reset-credentials") !== -1) return "reset";
    if (
      href.indexOf("openid-connect/auth") !== -1 ||
      href.indexOf("authenticate") !== -1 ||
      href.indexOf("login-actions/restart") !== -1
    ) {
      return "login";
    }
    return "";
  }

  function currentKind() {
    var card = document.querySelector(".login-pf-page > .card-pf");
    if (card) {
      if (card.querySelector("#kc-register-form")) return "register";
      if (card.querySelector("#kc-reset-password-form")) return "reset";
      if (card.querySelector("#kc-form-login")) return "login";
    }
    return kindFromUrl(location.href) || "login";
  }

  function slideDir(from, to) {
    if (!from || !to || from === to || ORDER[from] === undefined || ORDER[to] === undefined) return "";
    return ORDER[to] > ORDER[from] ? "forward" : "back";
  }

  var pageCache = new Map();

  function loadPage(href) {
    var cached = pageCache.get(href);
    if (cached) return cached;
    var request = fetch(href, { credentials: "same-origin", redirect: "follow" }).then(function (response) {
      if (!response.ok) throw new Error(String(response.status));
      return response.text().then(function (html) {
        return { html: html, url: response.url || href };
      });
    });
    pageCache.set(href, request);
    request.then(
      function () {
        window.setTimeout(function () { pageCache.delete(href); }, 1500);
      },
      function () { pageCache.delete(href); }
    );
    return request;
  }

  function bindPasswordToggles(root) {
    (root || document).querySelectorAll("[data-password-toggle]").forEach(function (button) {
      if (button.dataset.vigiaToggle) return;
      button.dataset.vigiaToggle = "1";
      button.addEventListener("click", function () {
        var input = document.getElementById(button.getAttribute("aria-controls"));
        if (!input) return;
        var reveal = input.type === "password";
        input.type = reveal ? "text" : "password";
        var icon = button.querySelector("i");
        if (icon) icon.className = reveal ? button.dataset.iconHide : button.dataset.iconShow;
        button.setAttribute("aria-label", reveal ? button.dataset.labelHide : button.dataset.labelShow);
      });
    });
  }

  var EMAIL_PATTERN = /^[\w.+-]+@([\w-]+\.)+[\w-]{2,}$/;
  var PHONE_PATTERN = /^[0-9+() .-]{8,16}$/;

  function linkRow(link) {
    return link.closest("#kc-form-options")
      || link.closest("#kc-info")
      || (link.parentElement && link.parentElement.tagName === "SPAN" && link.parentElement.parentElement
        ? link.parentElement.parentElement
        : link.parentElement);
  }

  function hideEmptyGroups(card) {
    card.querySelectorAll(".form-group").forEach(function (group) {
      if (group.querySelector("input, textarea, select, button")) return;
      if ((group.textContent || "").replace(/\s/g, "")) return;
      group.classList.add("vigia-collapsed");
    });
  }

  function takeLinks(card) {
    var box = document.createElement("div");
    if (!card) return box;
    card.querySelectorAll("a[href]").forEach(function (link) {
      if (link.closest("#kc-locale")) return;
      if (!kindFromUrl(link.href)) return;
      if (link.closest("#kc-form-login") && kindFromUrl(link.href) === "reset") return;
      var row = linkRow(link);
      if (!row || box.contains(row)) return;
      box.appendChild(row);
    });
    var info = card.querySelector("#kc-info");
    if (info && !box.contains(info)) box.appendChild(info);
    hideEmptyGroups(card);
    return box;
  }

  function mountDock(box) {
    var page = document.querySelector(".login-pf-page");
    if (!page || !box) return;
    var dock = page.querySelector(":scope > .vigia-auth-links");
    if (!dock) {
      dock = document.createElement("div");
      dock.className = "vigia-auth-links";
      page.appendChild(dock);
    }
    while (dock.firstChild) dock.removeChild(dock.firstChild);
    while (box.firstChild) dock.appendChild(box.firstChild);
    var viewport = page.querySelector(":scope > .vigia-slide-viewport");
    if (viewport) page.appendChild(dock);
  }

  function submitButton(form) {
    return form.querySelector("#kc-login, #kc-form-buttons input[type='submit'], #kc-form-buttons button[type='submit']");
  }

  function isFilled(input) {
    var type = (input.getAttribute("type") || "text").toLowerCase();
    if (type === "password") return (input.value || "").length > 0;
    return (input.value || "").trim().length > 0;
  }

  function formReady(form) {
    var inputs = Array.prototype.filter.call(
      form.querySelectorAll("input, textarea, select"),
      function (input) {
        var type = (input.getAttribute("type") || "").toLowerCase();
        return type !== "hidden" && type !== "submit" && type !== "button" && type !== "checkbox" && type !== "radio" && !input.disabled && !input.closest(".vigia-field--omit");
      }
    );
    if (!inputs.length) return false;
    var password = form.querySelector("input[name='password']");
    var confirm = form.querySelector("input[name='password-confirm']");
    for (var i = 0; i < inputs.length; i++) {
      var input = inputs[i];
      if (!isFilled(input)) return false;
      var id = (input.id || input.name || "").toLowerCase();
      var type = (input.getAttribute("type") || "").toLowerCase();
      if ((type === "email" || id === "email") && !EMAIL_PATTERN.test(input.value.trim())) return false;
      if ((type === "tel" || id === "phone") && !PHONE_PATTERN.test(input.value.trim())) return false;
    }
    if (password && confirm && password.value !== confirm.value) return false;
    return true;
  }

  function syncSubmit(root) {
    var forms;
    if (!root || root === document) {
      forms = document.querySelectorAll("form");
    } else if (root.tagName === "FORM") {
      forms = [root];
    } else {
      forms = root.querySelectorAll("form");
    }
    Array.prototype.forEach.call(forms, function (form) {
      var button = submitButton(form);
      if (!button) return;
      var ready = formReady(form);
      button.disabled = !ready;
      button.classList.toggle("vigia-cta--ready", ready);
    });
  }

  function slideTo(href, direction, historyMode) {
    if (document.documentElement.classList.contains("vigia-sliding")) return;
    var page = document.querySelector(".login-pf-page");
    var currentCard = page && page.querySelector(":scope > .card-pf");
    if (!page || !currentCard) {
      window.location.href = href;
      return;
    }

    document.documentElement.classList.add("vigia-sliding");
    loadPage(href).then(function (payload) {
      var doc = new DOMParser().parseFromString(payload.html, "text/html");
      var nextCard = doc.querySelector(".card-pf");
      if (!nextCard) throw new Error("missing card");

      var viewport = document.createElement("div");
      viewport.className = "vigia-slide-viewport";
      var track = document.createElement("div");
      track.className = "vigia-slide-track" + (direction === "back" ? " is-back" : "");

      function pane(card) {
        var el = document.createElement("div");
        el.className = "vigia-slide-pane";
        el.appendChild(card);
        return el;
      }

      var currentPane = pane(currentCard);
      var nextPane = pane(nextCard);
      if (direction === "forward") track.append(currentPane, nextPane);
      else track.append(nextPane, currentPane);

      viewport.appendChild(track);
      page.appendChild(viewport);
      var nextLinks = takeLinks(nextCard);
      run();
      softenLinks();
      var dock = page.querySelector(":scope > .vigia-auth-links");
      if (dock) page.appendChild(dock);

      var fromHeight = currentPane.offsetHeight;
      var toHeight = nextPane.offsetHeight;
      viewport.style.height = fromHeight + "px";
      track.getBoundingClientRect();

      var finished = false;
      function finish() {
        if (finished) return;
        finished = true;
        viewport.replaceWith(nextCard);
        if (doc.title) document.title = doc.title;
        if (historyMode === "push") history.pushState({ vigiaAuth: true }, "", payload.url);
        mountDock(nextLinks);
        run();
        softenLinks();
        bindPasswordToggles(nextCard);
        syncSubmit(document);
        bindPageSlides();
        document.documentElement.classList.remove("vigia-sliding");
      }

      track.addEventListener("transitionend", function (event) {
        if (event.target === track && event.propertyName === "transform") finish();
      });
      window.setTimeout(finish, SLIDE_MS + 80);

      requestAnimationFrame(function () {
        viewport.style.height = toHeight + "px";
        track.classList.add("is-slid");
      });
    }).catch(function () {
      document.documentElement.classList.remove("vigia-sliding");
      window.location.href = href;
    });
  }

  function bindPageSlides() {
    if (reduceMotion) return;
    document.querySelectorAll(".login-pf-page a[href]").forEach(function (link) {
      if (link.dataset.vigiaSlide) return;
      var direction = slideDir(currentKind(), kindFromUrl(link.href));
      if (!direction) return;
      link.dataset.vigiaSlide = "1";
      link.addEventListener("pointerenter", function () { loadPage(link.href); });
      link.addEventListener("pointerdown", function () { loadPage(link.href); });
      link.addEventListener("click", function (event) {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        if (document.documentElement.classList.contains("vigia-sliding")) {
          event.preventDefault();
          return;
        }
        var nextDirection = slideDir(currentKind(), kindFromUrl(link.href));
        if (!nextDirection) return;
        event.preventDefault();
        slideTo(link.href, nextDirection, "push");
      });
    });
  }

  window.addEventListener("popstate", function () {
    if (reduceMotion) return;
    if (kindFromUrl(location.href) === currentKind()) return;
    var direction = slideDir(currentKind(), kindFromUrl(location.href)) || "back";
    slideTo(location.href, direction, "none");
  });

  var TEXT_TYPES = ["text", "password", "email", "tel", "url", "search", "number"];

  function isTextField(input) {
    if (!input) return false;
    var tag = input.tagName;
    if (tag === "TEXTAREA" || tag === "SELECT") return true;
    if (tag !== "INPUT") return false;
    var type = (input.getAttribute("type") || "text").toLowerCase();
    return TEXT_TYPES.indexOf(type) !== -1;
  }

  function fieldLabel(group) {
    return group.querySelector(":scope > label.pf-c-form__label, :scope > div > label.pf-c-form__label");
  }

  function fieldInput(group) {
    return group.querySelector("input.pf-c-form-control, textarea.pf-c-form-control, select.pf-c-form-control");
  }

  function stripAsterisk(label) {
    var parent = label.parentElement;
    if (!parent) return;
    Array.prototype.forEach.call(parent.childNodes, function (node) {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.replace(/\s/g, "") === "*") {
        node.textContent = "";
      }
    });
  }

  function iconKind(group, input) {
    var type = (input.getAttribute("type") || "text").toLowerCase();
    var id = (input.id || "").toLowerCase();
    var name = (input.name || "").toLowerCase();
    if (type === "password") return "password";
    if (type === "email" || id === "email" || name === "email") return "email";
    if (type === "tel" || id === "phone" || name === "phone") return "phone";
    var onRegister = !!group.closest("#kc-register-form");
    if (onRegister && (id === "username" || id === "firstname" || id === "lastname" || name === "firstname" || name === "lastname")) {
      return "user";
    }
    if (id === "username" || name === "username") return "email";
    if (id === "firstname" || id === "lastname" || name === "firstname" || name === "lastname") return "user";
    return "";
  }

  function sync(group, input) {
    var floated = document.activeElement === input || !!(input.value && input.value.length);
    group.classList.toggle("vigia-field--float", floated);
  }

  function enhance(group) {
    if (group.classList.contains("vigia-field")) return;
    var input = fieldInput(group);
    var label = fieldLabel(group);
    if (!input || !label || !isTextField(input)) return;

    group.classList.add("vigia-field");
    var kind = iconKind(group, input);
    if (kind) {
      group.classList.add("vigia-field--icon", "vigia-field--" + kind);
    }
    if (kind === "phone") {
      input.setAttribute("autocomplete", "tel");
      input.setAttribute("inputmode", "tel");
    }
    stripAsterisk(label);

    var update = function () {
      sync(group, input);
    };
    input.addEventListener("input", update);
    input.addEventListener("change", update);
    input.addEventListener("focus", update);
    input.addEventListener("blur", update);
    update();
  }

  var REGISTER_SLOTS = {
    firstname: { order: "1", half: true },
    lastname: { order: "2", half: true },
    email: { order: "3", half: false },
    phone: { order: "4", half: false },
    password: { order: "5", half: true },
    "password-confirm": { order: "6", half: true }
  };

  function layoutRegister(root) {
    (root || document).querySelectorAll("#kc-register-form").forEach(function (form) {
      Array.prototype.forEach.call(form.querySelectorAll(":scope > .form-group"), function (group) {
        var input = group.querySelector("input:not([type='hidden']):not([type='submit']), textarea, select");
        var holder = group.querySelector("#kc-form-buttons");
        if (!input) {
          if (holder) group.style.order = "7";
          return;
        }
        var key = (input.id || input.name || "").toLowerCase();
        if (key === "username") {
          group.classList.add("vigia-field--omit");
          input.tabIndex = -1;
          input.setAttribute("aria-hidden", "true");
          return;
        }
        var slot = REGISTER_SLOTS[key];
        if (!slot) return;
        group.style.order = slot.order;
        group.classList.toggle("vigia-span-half", slot.half);
      });
    });
  }

  function mirrorRegisterUsername(form) {
    if (!form || form.id !== "kc-register-form") return;
    var username = form.querySelector("input[name='username']");
    var email = form.querySelector("input[name='email']");
    if (!username || !email || !username.closest(".vigia-field--omit")) return;
    username.value = email.value.trim();
  }

  function layoutLoginOptions(root) {
    (root || document).querySelectorAll("#kc-form-login").forEach(function (form) {
      var forgot = form.querySelector('a[href*="reset-credentials"]');
      var remember = form.querySelector("#rememberMe");
      if (!forgot && !remember) return;

      var row = form.querySelector(".vigia-login-settings");
      if (!row) {
        row = document.createElement("div");
        row.className = "vigia-login-settings";
        var buttons = form.querySelector("#kc-form-buttons");
        if (buttons) form.insertBefore(row, buttons);
        else form.appendChild(row);
      }

      if (remember) {
        var box = remember.closest(".checkbox") || remember.closest("label");
        if (box && box.parentElement !== row) row.appendChild(box);
      }

      if (forgot) {
        forgot.classList.add("vigia-forgot");
        if (forgot.parentElement !== row) row.appendChild(forgot);
      }

      hideEmptyGroups(form.closest(".card-pf") || form);
    });
  }

  function vigiaMessages() {
    var node = document.getElementById("vigia-messages");
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return null;
    }
  }

  function polishResetBack(root) {
    var scope = root || document;
    if (!scope.querySelector || !scope.querySelector("#kc-reset-password-form")) return;
    var copy = vigiaMessages();
    if (!copy || !copy.remembered || !copy.signIn) return;
    scope.querySelectorAll("a[href]").forEach(function (link) {
      if (kindFromUrl(link.href) !== "login" || link.dataset.vigiaPrompt) return;
      link.dataset.vigiaPrompt = "1";
      link.textContent = copy.signIn;
      var hint = document.createElement("span");
      hint.className = "vigia-auth-hint";
      hint.textContent = copy.remembered;
      link.parentElement.insertBefore(hint, link);
    });
  }

  function run() {
    document.querySelectorAll(".login-pf-page .form-group").forEach(enhance);
    layoutRegister(document);
    layoutLoginOptions(document);
    polishResetBack(document);
  }

  function softenLinks() {
    document.querySelectorAll(".login-pf-page a").forEach(function (link) {
      var text = link.textContent.replace(/^\s*«\s*/, "").replace(/\s*»\s*$/, "");
      if (text !== link.textContent) link.textContent = text;
    });
  }

  function boot() {
    run();
    var card = document.querySelector(".login-pf-page > .card-pf");
    mountDock(takeLinks(card));
    syncSubmit(document);
    softenLinks();
    bindPageSlides();
  }

  document.addEventListener("input", function (event) {
    var form = event.target && event.target.closest && event.target.closest("form");
    if (!form) return;
    mirrorRegisterUsername(form);
    syncSubmit(form);
  });

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.closest || !form.closest(".login-pf-page")) return;
    mirrorRegisterUsername(form);
    syncSubmit(form);
    var button = submitButton(form);
    if (button && button.disabled) event.preventDefault();
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.setTimeout(function () {
    run();
    syncSubmit(document);
  }, 300);
})();
