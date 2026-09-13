(function () {
  "use strict";

  // Footer copyright year
  document.querySelectorAll("#footerYear").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  // Mobile nav toggle
  var menuToggle = document.getElementById("mobileMenuToggle");
  var primaryNav = document.getElementById("primaryNav");
  var navOverlay = document.getElementById("navOverlay");

  function closeNav() {
    if (primaryNav) primaryNav.classList.remove("is-open");
    if (navOverlay) navOverlay.classList.remove("is-visible");
  }

  if (menuToggle && primaryNav) {
    menuToggle.addEventListener("click", function () {
      primaryNav.classList.toggle("is-open");
      if (navOverlay) navOverlay.classList.toggle("is-visible");
    });
  }
  if (navOverlay) {
    navOverlay.addEventListener("click", closeNav);
  }

  // "Bài viết" nav dropdown
  document.querySelectorAll(".nav-item").forEach(function (navItem) {
    var caret = navItem.querySelector(".nav-caret");
    if (!caret) return;
    caret.addEventListener("click", function (e) {
      e.preventDefault();
      var open = navItem.classList.toggle("is-open");
      caret.setAttribute("aria-expanded", String(open));
    });
  });
  document.addEventListener("click", function (e) {
    document.querySelectorAll(".nav-item.is-open").forEach(function (navItem) {
      if (!navItem.contains(e.target)) {
        navItem.classList.remove("is-open");
        var caret = navItem.querySelector(".nav-caret");
        if (caret) caret.setAttribute("aria-expanded", "false");
      }
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".nav-item.is-open").forEach(function (navItem) {
        navItem.classList.remove("is-open");
        var caret = navItem.querySelector(".nav-caret");
        if (caret) caret.setAttribute("aria-expanded", "false");
      });
    }
  });

  // Search modal (Ctrl+K / Cmd+K) — tìm theo tiêu đề hoặc tag trong SITE_SEARCH_INDEX.
  var searchToggles = document.querySelectorAll(".search-toggle");
  var searchModal = document.getElementById("searchModal");
  var searchOverlay = document.getElementById("searchModalOverlay");
  var searchForm = document.getElementById("searchForm");
  var searchInput = document.getElementById("siteSearch");
  var searchResults = document.getElementById("searchResults");
  var searchEmpty = document.getElementById("searchEmpty");

  if (searchModal && searchInput && searchResults) {
    var searchIndex = window.SITE_SEARCH_INDEX || [];
    var activeIndex = -1;
    var lastFocused = null;

    function stripDiacritics(str) {
      return str
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D");
    }

    function normalize(str) {
      return stripDiacritics(String(str || "")).toLowerCase().trim();
    }

    function renderResults(items) {
      searchResults.innerHTML = "";
      activeIndex = -1;
      if (!items.length) {
        if (searchEmpty) searchEmpty.hidden = false;
        return;
      }
      if (searchEmpty) searchEmpty.hidden = true;
      items.forEach(function (item, i) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = item.url;
        a.className = "search-modal-result";
        a.setAttribute("data-index", String(i));

        var title = document.createElement("span");
        title.className = "search-result-title";
        title.textContent = item.title;

        var meta = document.createElement("span");
        meta.className = "search-result-meta";
        meta.textContent = item.pillar ? item.type + " — " + item.pillar : item.type;

        a.appendChild(title);
        a.appendChild(meta);
        li.appendChild(a);
        searchResults.appendChild(li);
      });
    }

    function search(query) {
      var q = normalize(query);
      if (!q) return searchIndex.slice(0, 8);
      return searchIndex.filter(function (item) {
        var haystack = normalize(item.title + " " + (item.pillar || "") + " " + item.tags.join(" "));
        return haystack.indexOf(q) !== -1;
      });
    }

    function setActive(index) {
      var options = searchResults.querySelectorAll(".search-modal-result");
      options.forEach(function (opt) { opt.classList.remove("is-active"); });
      if (index >= 0 && index < options.length) {
        activeIndex = index;
        options[index].classList.add("is-active");
        options[index].scrollIntoView({ block: "nearest" });
      } else {
        activeIndex = -1;
      }
    }

    function openSearchModal() {
      lastFocused = document.activeElement;
      searchModal.classList.add("is-open");
      searchModal.hidden = false;
      document.body.classList.add("search-modal-open");
      searchToggles.forEach(function (toggle) { toggle.setAttribute("aria-expanded", "true"); });
      renderResults(search(""));
      searchInput.value = "";
      searchInput.focus();
    }

    function closeSearchModal() {
      searchModal.classList.remove("is-open");
      searchModal.hidden = true;
      document.body.classList.remove("search-modal-open");
      searchToggles.forEach(function (toggle) { toggle.setAttribute("aria-expanded", "false"); });
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }

    searchToggles.forEach(function (toggle) {
      toggle.addEventListener("click", function () {
        if (searchModal.classList.contains("is-open")) closeSearchModal();
        else openSearchModal();
      });
    });

    if (searchOverlay) searchOverlay.addEventListener("click", closeSearchModal);
    if (searchForm) {
      searchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var options = searchResults.querySelectorAll(".search-modal-result");
        var target = activeIndex >= 0 ? options[activeIndex] : options[0];
        if (target) window.location.href = target.getAttribute("href");
      });
    }

    searchInput.addEventListener("input", function () {
      renderResults(search(searchInput.value));
    });

    searchInput.addEventListener("keydown", function (e) {
      var options = searchResults.querySelectorAll(".search-modal-result");
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive(activeIndex + 1 >= options.length ? 0 : activeIndex + 1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive(activeIndex - 1 < 0 ? options.length - 1 : activeIndex - 1);
      }
    });

    document.addEventListener("keydown", function (e) {
      var isCombo = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k";
      if (isCombo) {
        e.preventDefault();
        if (searchModal.classList.contains("is-open")) closeSearchModal();
        else openSearchModal();
      } else if (e.key === "Escape" && searchModal.classList.contains("is-open")) {
        closeSearchModal();
      }
    });
  }

  // Newsletter form (demo — no backend)
  var newsletterForm = document.getElementById("newsletterForm");
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var note = document.getElementById("newsletterNote");
      var email = newsletterForm.querySelector('input[name="email_address"]').value;
      if (note) {
        note.textContent = "Cảm ơn! Đã thêm " + email + " vào danh sách. (Chỉ là demo — không có email nào thực sự được gửi.)";
      }
      newsletterForm.reset();
    });
  }

  // Pay-what-you-want form (demo — no backend)
  var pwywForm = document.getElementById("pwywForm");
  if (pwywForm) {
    pwywForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = pwywForm.querySelector('input[name="price"]');
      window.alert("Cảm ơn bạn đã ủng hộ! (Đã chọn " + input.value + "₫/năm). Đây là demo — chưa có khoản thanh toán nào được xử lý.");
    });
  }

  // "See older articles" — chỉ hiện khi trang chủ có hơn 5 bài
  var pagination = document.getElementById("pagination");
  var articleList = document.getElementById("articleList");
  if (pagination && articleList && articleList.querySelectorAll(".article-item").length > 5) {
    pagination.hidden = false;
  }

  // "See older articles" — demo pagination
  var loadMoreBtn = document.getElementById("loadMoreBtn");
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", function (e) {
      e.preventDefault();
      loadMoreBtn.textContent = "Bạn đã xem hết bài viết (demo)";
      loadMoreBtn.style.pointerEvents = "none";
      loadMoreBtn.style.opacity = "0.6";
    });
  }

  // Login popup (opens as a modal over the current page instead of navigating away)
  var authModal = document.getElementById("authModal");
  if (authModal) {
    var authModalClose = document.getElementById("authModalClose");
    var authModalBackdrop = document.getElementById("authModalBackdrop");

    var openAuthModal = function () {
      authModal.classList.add("is-open");
      document.body.classList.add("auth-modal-open");
      var emailInput = document.getElementById("email");
      if (emailInput) emailInput.focus();
    };
    var closeAuthModal = function () {
      authModal.classList.remove("is-open");
      document.body.classList.remove("auth-modal-open");
    };

    document.querySelectorAll(".nav-login").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        openAuthModal();
      });
    });
    if (authModalClose) authModalClose.addEventListener("click", closeAuthModal);
    if (authModalBackdrop) authModalBackdrop.addEventListener("click", closeAuthModal);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && authModal.classList.contains("is-open")) closeAuthModal();
    });
  }

  // Login / Sign up toggle (demo — no backend auth)
  var authForm = document.getElementById("authForm");
  if (authForm) {
    var authTitle = document.getElementById("authTitle");
    var authSub = document.getElementById("authSub");
    var authSubmit = document.getElementById("authSubmit");
    var nameField = document.getElementById("nameField");
    var forgotRow = document.getElementById("forgotRow");
    var authSwitch = document.getElementById("authSwitch");
    var switchToSignup = document.getElementById("switchToSignup");
    var authError = document.getElementById("authError");
    var isSignup = false;

    function renderMode() {
      if (isSignup) {
        authTitle.textContent = "Tạo tài khoản của bạn";
        authSub.textContent = "Đăng ký để lưu bài viết và quản lý gói thành viên.";
        authSubmit.textContent = "Đăng ký";
        nameField.style.display = "block";
        document.getElementById("fullName").required = true;
        forgotRow.style.display = "none";
        authSwitch.innerHTML = 'Đã có tài khoản? <a href="#" id="switchToSignup">Đăng nhập</a>';
      } else {
        authTitle.textContent = "Đăng nhập";
        authSub.textContent = "Chào mừng bạn quay lại. Truy cập nội dung thành viên bên dưới.";
        authSubmit.textContent = "Đăng nhập";
        nameField.style.display = "none";
        document.getElementById("fullName").required = false;
        forgotRow.style.display = "block";
        authSwitch.innerHTML = 'Chưa có tài khoản? <a href="#" id="switchToSignup">Đăng ký</a>';
      }
      authError.classList.remove("is-visible");
      document.getElementById("switchToSignup").addEventListener("click", handleSwitchClick);
    }

    function handleSwitchClick(e) {
      e.preventDefault();
      isSignup = !isSignup;
      renderMode();
    }

    if (switchToSignup) {
      switchToSignup.addEventListener("click", handleSwitchClick);
    }

    authForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = document.getElementById("email").value.trim();
      var password = document.getElementById("password").value.trim();
      var name = document.getElementById("fullName").value.trim();

      if (!email || !password || (isSignup && !name)) {
        authError.textContent = "Vui lòng điền đầy đủ thông tin để tiếp tục.";
        authError.classList.add("is-visible");
        return;
      }
      authError.classList.remove("is-visible");
      window.alert((isSignup ? "Đã tạo tài khoản" : "Đã đăng nhập") + " cho " + email + ". Đây là form demo — không có xác thực thực sự nào diễn ra.");
      authForm.reset();
    });
  }
})();
