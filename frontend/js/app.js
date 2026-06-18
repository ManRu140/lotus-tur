const API_BASE = "https://lotus-tur-production-23c6.up.railway.app";

let isUserLoggedIn = false;
let currentLang = "RU";
let isGridViewActive = false;
let currentAuthMode = "login";

const _todayForCalendar = new Date();
let calYear = _todayForCalendar.getFullYear();
let calMonth = _todayForCalendar.getMonth();
let selectedDateStr = "";

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function apiFetch(path, options = {}) {
  // SECURITY FIX: no longer reads a token from localStorage and sends it
  // as a Bearer header. The backend already accepts the httpOnly
  // `access_token` cookie (see app/core/deps.py), which JS can never
  // read — keeping a copy of the JWT in localStorage only gave any
  // future XSS bug a portable, long-lived credential to steal for free.
  const csrfToken = getCookie("csrf_token");
  const headers = {
    "Content-Type": "application/json",
    ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    ...options.headers,
  };
  const res = await fetch(API_BASE + path, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Ошибка ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

async function checkExistingSession() {
  // The `access_token` is httpOnly so JS can never read it, but the
  // `csrf_token` cookie IS readable and is only set when a session
  // exists. Skipping the /api/auth/me request when it's absent avoids
  // a noisy 401 in the browser console for every anonymous visitor
  // (the browser logs the failed fetch before our catch() can run,
  // which looks alarming even though it's completely expected behaviour).
  if (!getCookie("csrf_token")) {
    // Clear any stale localStorage state left from a previous session
    // that ended (cookie expired/cleared) so the UI doesn't show a
    // phantom logged-in name.
    localStorage.removeItem("username");
    localStorage.removeItem("avatar_url");
    localStorage.removeItem("full_name");
    return;
  }

  const savedName = localStorage.getItem("username");
  const savedAvatar = localStorage.getItem("avatar_url");
  const savedFull = localStorage.getItem("full_name");

  if (savedName) {
    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = savedFull || savedName;
    const subEl = document.getElementById("profileSub");
    if (subEl) subEl.textContent = savedName;
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl && savedAvatar) avatarEl.src = savedAvatar;
  }

  try {
    const data = await apiFetch("/api/auth/me");
    if (data && data.username) {
      isUserLoggedIn = true;
      localStorage.setItem("username", data.username);
      if (data.avatar_url) localStorage.setItem("avatar_url", data.avatar_url);
      if (data.full_name) localStorage.setItem("full_name", data.full_name);

      const nameEl = document.getElementById("profileName");
      if (nameEl) nameEl.textContent = data.full_name || data.username;
      const subEl = document.getElementById("profileSub");
      if (subEl) subEl.textContent = data.username;
      const avatarEl = document.getElementById("profileAvatar");
      if (avatarEl && data.avatar_url) avatarEl.src = data.avatar_url;

      loadProfileData();
    }
  } catch {
    // Session cookie exists but the token is expired or invalid on the
    // backend. Clear everything so we don't keep making 401 requests
    // on this page load (bookings, achievements, profile/me all check
    // isUserLoggedIn, so this prevents the cascade of 401s).
    localStorage.removeItem("username");
    localStorage.removeItem("avatar_url");
    localStorage.removeItem("full_name");
    isUserLoggedIn = false;
    // Best-effort: tell the server to clear the cookies too so the
    // stale csrf_token doesn't keep triggering this on every reload.
    fetch(API_BASE + "/api/auth/logout", {
      method: "POST",
      credentials: "include",
    }).catch(() => {});
  }
}

async function loadProfileData() {
  if (!isUserLoggedIn) return;

  try {
    const profile = await apiFetch("/api/profile/me");

    localStorage.setItem("username", profile.username);
    if (profile.avatar_url)
      localStorage.setItem("avatar_url", profile.avatar_url);
    if (profile.full_name) localStorage.setItem("full_name", profile.full_name);

    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = profile.full_name || profile.username;

    const subEl = document.getElementById("profileSub");
    if (subEl) subEl.textContent = profile.email || profile.username;

    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl && profile.avatar_url) avatarEl.src = profile.avatar_url;

    try {
      const refData = await apiFetch("/api/promo/ref");
      const refInp = document.getElementById("refLink");
      if (refInp && refData.link) refInp.value = refData.link;
    } catch {}
  } catch (e) {}

  loadMyBookings();
  loadMyAchievements();
}

async function loadMyBookings() {
  try {
    const bookings = await apiFetch("/api/bookings/my");
    renderUserTours(
      bookings.map((b) => {
        const ref =
          typeof toursData !== "undefined"
            ? toursData.find((t) => t.id === b.tour_id)
            : null;
        return {
          id: b.tour_id,
          name: b.tour_name,
          date: b.tour_date,
          status: b.status,
          price: ref ? ref.price : "—",
          img: ref
            ? ref.img
            : "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80",
          booking_id: b.id,
        };
      }),
    );
  } catch (e) {
    if (typeof mockUserTours !== "undefined") renderUserTours(mockUserTours);
  }
}

async function loadMyAchievements() {
  try {
    const achievements = await apiFetch("/api/profile/achievements");
    renderAchievements(achievements);
  } catch (e) {
    if (typeof achievementsList !== "undefined")
      renderAchievements(achievementsList);
  }
}

// ? Validates email format client-side
function _isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ? Checks min password strength: 8+ chars, uppercase, digit
function _checkPasswordStrength(password) {
  if (password.length < 8) return "Пароль — минимум 8 символов";
  if (!/[A-Z]/.test(password)) return "Добавьте хотя бы одну заглавную букву";
  if (!/\d/.test(password)) return "Добавьте хотя бы одну цифру";
  return null;
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("authLoginInput").value.trim();
  const password = document.getElementById("authPasswordInput").value;

  if (!username || !password) {
    showToast("Заполните все поля.", "error");
    return;
  }

  if (currentAuthMode === "register") {
    const email = document.getElementById("authEmailInput").value.trim();
    if (!email) {
      showToast("Введите email.", "error");
      return;
    }
    if (!_isValidEmail(email)) {
      showToast("Введите корректный email.", "error");
      return;
    }

    const strengthErr = _checkPasswordStrength(password);
    if (strengthErr) {
      showToast(strengthErr, "error");
      return;
    }

    const passConfirm = document.getElementById(
      "authPasswordConfirmInput",
    ).value;
    if (password !== passConfirm) {
      showToast("Пароли не совпадают!", "error");
      return;
    }
  }

  const btn = document.getElementById("authSubmitBtn");
  const originalText = btn ? btn.textContent : "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳";
  }

  try {
    let data;
    if (currentAuthMode === "login") {
      const res = await fetch(API_BASE + "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Неверное имя пользователя или пароль");
      }
      data = await res.json();
    } else {
      const email = document.getElementById("authEmailInput").value.trim();
      const res = await fetch(API_BASE + "/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Ошибка регистрации");
      }
      data = await res.json();
    }

    _applyLoginData(data);
    toggleAuthModal();
    showToast(
      currentAuthMode === "login"
        ? "Добро пожаловать! 👋"
        : "Аккаунт создан! 🎉",
      "success",
    );
    setTimeout(() => {
      toggleProfile();
      loadProfileData();
    }, 300);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

function _applyLoginData(data) {
  localStorage.setItem("username", data.username);
  if (data.avatar_url) localStorage.setItem("avatar_url", data.avatar_url);
  if (data.full_name) localStorage.setItem("full_name", data.full_name);

  isUserLoggedIn = true;

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = data.full_name || data.username;

  const subEl = document.getElementById("profileSub");
  if (subEl) subEl.textContent = data.username;

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl && data.avatar_url) avatarEl.src = data.avatar_url;
}

function handleLogout() {
  fetch(API_BASE + "/api/auth/logout", {
    method: "POST",
    credentials: "include",
  }).catch(() => {});

  isUserLoggedIn = false;
  localStorage.removeItem("username");
  localStorage.removeItem("avatar_url");
  localStorage.removeItem("full_name");

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = "Войти";

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl) {
    avatarEl.src =
      "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80";
  }

  document.getElementById("sideProfile")?.classList.remove("open");
  showToast(
    currentLang === "RU"
      ? "Вы вышли из аккаунта."
      : "You have been logged out.",
  );
}

async function loginWithVK() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/vk/client-id`);
    if (!res.ok) {
      showToast("VK OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    const state = crypto.randomUUID();
    sessionStorage.setItem("oauth_state", state);
    sessionStorage.setItem("oauth_provider", "vk");

    const redirectUri = encodeURIComponent(
      window.location.origin + "/index.html",
    );
    const url =
      `https://id.vk.com/authorize` +
      `?response_type=code` +
      `&client_id=${client_id}` +
      `&redirect_uri=${redirectUri}` +
      `&scope=email` +
      `&state=${encodeURIComponent(state)}`;

    window.location.href = url;
  } catch (err) {
    showToast("Не удалось подключиться к серверу.");
  }
}

async function loginWithGoogle() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/google/client-id`);
    if (!res.ok) {
      showToast("Google OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    const state = crypto.randomUUID();
    const REDIRECT_URI = window.location.origin + "/index.html";

    sessionStorage.setItem("oauth_state", state);
    sessionStorage.setItem("oauth_provider", "google");

    sessionStorage.setItem("oauth_redirect_uri", REDIRECT_URI);

    const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    url.searchParams.set("client_id", client_id);
    url.searchParams.set("redirect_uri", REDIRECT_URI);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", "openid email profile");
    url.searchParams.set("access_type", "online");
    url.searchParams.set("state", state);

    window.location.href = url.toString();
  } catch (err) {
    showToast("Не удалось подключиться к серверу.");
  }
}

async function handleGoogleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  const state = params.get("state");
  const error = params.get("error");
  const provider = sessionStorage.getItem("oauth_provider") || "google";

  if (!code && !error) return;

  window.history.replaceState({}, "", window.location.pathname);

  if (error) {
    showToast("Ошибка входа: " + error);
    return;
  }

  const savedState = sessionStorage.getItem("oauth_state");
  const redirectUri = sessionStorage.getItem("oauth_redirect_uri");
  sessionStorage.removeItem("oauth_state");
  sessionStorage.removeItem("oauth_provider");
  sessionStorage.removeItem("oauth_redirect_uri");

  if (!state || state !== savedState) {
    showToast("Ошибка безопасности OAuth. Попробуйте снова.");
    return;
  }

  let endpoint;
  if (provider === "vk") {
    endpoint = `/api/auth/vk/callback?code=${encodeURIComponent(code)}`;
  } else {
    const uriParam = redirectUri
      ? `&redirect_uri=${encodeURIComponent(redirectUri)}`
      : "";
    endpoint = `/api/auth/google/callback?code=${encodeURIComponent(code)}${uriParam}`;
  }

  try {
    const res = await fetch(API_BASE + endpoint, { credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast("Ошибка авторизации: " + (err.detail || "неизвестная ошибка"));
      return;
    }

    const data = await res.json();
    _applyLoginData(data);

    const authModal = document.getElementById("authModal");
    if (authModal) authModal.classList.remove("open");

    setTimeout(() => {
      if (typeof toggleProfile === "function") toggleProfile();
      loadProfileData();
    }, 300);
  } catch (err) {
    showToast("Не удалось подключиться к серверу.");
  }
}

async function loadAvatarFromPC(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];

  const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
  if (!allowedTypes.includes(file.type)) {
    showToast("Допустимые форматы: JPEG, PNG, WEBP, GIF");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast("Файл слишком большой. Максимум: 5MB");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl) avatarEl.src = dataUrl;
  };
  reader.readAsDataURL(file);
}

async function saveNicknameToAPI(newUsername) {
  try {
    const data = await apiFetch("/api/profile/username", {
      method: "PATCH",
      body: JSON.stringify({ username: newUsername }),
    });
    localStorage.setItem("username", data.username);
    showToast("Никнейм обновлён!");
  } catch (e) {
    showToast("Ошибка: " + e.message);

    const nameEl = document.getElementById("profileName");
    const saved = localStorage.getItem("username");
    if (nameEl && saved) nameEl.textContent = saved;
  }
}

/* ─── WEEKLY SCHEDULE ─────────────────────────────── */
(function buildSchedule() {
  const DAYS = [
    { key: "Понедельник", full: "Понедельник" },
    { key: "Вторник", full: "Вторник" },
    { key: "Среда", full: "Среда" },
    { key: "Четверг", full: "Четверг" },
    { key: "Пятница", full: "Пятница" },
  ];

  const todayIdx = (new Date().getDay() + 6) % 7; // 0=Пн

  const grid = document.getElementById("weekGrid");
  if (!grid || typeof toursData === "undefined") return;

  function makeTourCard(t) {
    const card = document.createElement("div");
    card.className = "schedule-tour-card";
    card.innerHTML =
      '<div class="schedule-tour-time">' +
      (t.departure !== "Ежедневно" ? t.departure : "По расписанию") +
      "</div>" +
      '<div class="schedule-tour-name">' +
      t.name +
      "</div>" +
      '<div class="schedule-tour-price">от ' +
      t.price +
      " ₽</div>" +
      '<div class="schedule-tour-duration">' +
      t.duration +
      "</div>";
    card.addEventListener("click", function () {
      const bookSelect = document.getElementById("bookTourSelect");
      if (bookSelect) bookSelect.value = t.id;
      if (typeof openBookingGeneral === "function") {
        openBookingGeneral();
      } else {
        const modal = document.getElementById("bookingModal");
        if (modal) modal.classList.add("open");
      }
    });
    return card;
  }

  // Будние дни Пн–Пт — показываем только туры, привязанные именно к этому дню
  DAYS.forEach(function (day, i) {
    const col = document.createElement("div");
    col.className = "week-col";

    const header = document.createElement("div");
    header.className =
      "week-day-header" + (i === todayIdx ? " today" : "") + " day-glow";
    header.textContent = day.full;
    if (i === todayIdx) header.title = "Сегодня";
    col.appendChild(header);

    const toursForDay = toursData.filter(function (t) {
      return t.schedule === day.key;
    });

    if (toursForDay.length === 0) {
      const empty = document.createElement("div");
      empty.className = "week-col-empty";
      empty.textContent = "Нет отдельных туров";
      col.appendChild(empty);
    } else {
      toursForDay.forEach(function (t) {
        col.appendChild(makeTourCard(t));
      });
    }

    grid.appendChild(col);
  });

  // Колонка "Каждый день" — туры, доступные ежедневно
  const dailyCol = document.getElementById("dailyToursCol");
  if (dailyCol) {
    const dailyTours = toursData.filter(function (t) {
      return t.schedule === "Ежедневно";
    });
    dailyTours.forEach(function (t) {
      dailyCol.appendChild(makeTourCard(t));
    });
  }

  // Отдельная плашка "Выходные туры" — Субота + Воскресенье вместе
  const weekendWrap = document.getElementById("weekendBlock");
  if (weekendWrap) {
    const satTours = toursData.filter(function (t) {
      return t.schedule === "Суббота";
    });
    const sunTours = toursData.filter(function (t) {
      return t.schedule === "Воскресенье";
    });

    const satCol = document.createElement("div");
    satCol.className = "weekend-col";
    const satHeader = document.createElement("div");
    satHeader.className =
      "weekend-day-header" + (todayIdx === 5 ? " today" : "");
    satHeader.textContent = "Суббота";
    satCol.appendChild(satHeader);
    satTours.forEach(function (t) {
      satCol.appendChild(makeTourCard(t));
    });

    const sunCol = document.createElement("div");
    sunCol.className = "weekend-col";
    const sunHeader = document.createElement("div");
    sunHeader.className =
      "weekend-day-header" + (todayIdx === 6 ? " today" : "");
    sunHeader.textContent = "Воскресенье";
    sunCol.appendChild(sunHeader);
    sunTours.forEach(function (t) {
      sunCol.appendChild(makeTourCard(t));
    });

    weekendWrap.appendChild(satCol);
    weekendWrap.appendChild(sunCol);
  }
})();
