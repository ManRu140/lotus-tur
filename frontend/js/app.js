/**
 * app.js — Основная логика приложения
 *
 * Исправления:
 *  [FIX-1] Убран mock-логин: больше нельзя войти под любым именем/паролем.
 *          При недоступности бэкенда — ошибка, не фантомный вход.
 *  [FIX-2] Личный кабинет загружает реальные данные с API.
 *  [FIX-3] VK OAuth использует /api/auth/vk/client-id (как Google).
 *  [FIX-4] state проверка для обоих OAuth провайдеров.
 */

const API_BASE = "https://lotus-tur-production-23c6.up.railway.app";

let isUserLoggedIn   = false;
let currentLang      = "RU";
let isGridViewActive = false;
let currentAuthMode  = "login";

let calYear         = 2026;
let calMonth        = 5;
let selectedDateStr = "";

let cachedToursData = [];

// ─── API-хелпер (HttpOnly Cookie, без localStorage токена) ──────────────────
async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const res = await fetch(API_BASE + path, { ...options, headers, credentials: "include" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Ошибка ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

// ─── Проверка сессии при загрузке ───────────────────────────────────────────
async function checkExistingSession() {
  try {
    const data = await apiFetch("/api/auth/me");
    if (data && data.username) {
      isUserLoggedIn = true;
      localStorage.setItem("username", data.username);
      const el = document.getElementById("profileName");
      if (el) el.textContent = data.username;
      // Загружаем полный профиль если панель открыта
      loadProfileData();
    }
  } catch {
    // Нет сессии — норма
  }
}

// ─── Загрузка данных личного кабинета ───────────────────────────────────────
async function loadProfileData() {
  if (!isUserLoggedIn) return;

  try {
    // Профиль
    const profile = await apiFetch("/api/profile/me");
    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = profile.username;
    localStorage.setItem("username", profile.username);

    const subEl = document.getElementById("profileSub");
    if (subEl) subEl.textContent = profile.email || "Участник клуба";

    if (profile.avatar_url) {
      const avatarEl = document.getElementById("profileAvatar");
      if (avatarEl) avatarEl.src = profile.avatar_url;
    }

    // Реферальная ссылка
    try {
      const refData = await apiFetch("/api/promo/ref");
      const refInp = document.getElementById("refLink");
      if (refInp && refData.link) refInp.value = refData.link;
    } catch {}

  } catch (e) {
    console.warn("Не удалось загрузить профиль:", e.message);
  }

  // Бронирования пользователя
  loadMyBookings();

  // Достижения
  loadMyAchievements();
}

// ─── Загрузка реальных бронирований ─────────────────────────────────────────
async function loadMyBookings() {
  try {
    const bookings = await apiFetch("/api/bookings/my");
    renderUserTours(bookings.map(b => ({
      id: b.tour_id,
      name: b.tour_name,
      date: b.tour_date,
      status: b.status,
      price: "",
      img: "",
      booking_id: b.id,
    })));
  } catch (e) {
    console.warn("Не удалось загрузить бронирования:", e.message);
    if (typeof mockUserTours !== "undefined") renderUserTours(mockUserTours);
  }
}

// ─── Загрузка реальных достижений ───────────────────────────────────────────
async function loadMyAchievements() {
  try {
    const achievements = await apiFetch("/api/profile/achievements");
    renderAchievements(achievements.map(a => ({
      icon: a.icon,
      titleRu: a.title,
      descRu: a.description,
      unlocked: a.unlocked,
    })));
  } catch (e) {
    console.warn("Не удалось загрузить достижения:", e.message);
    if (typeof achievementsList !== "undefined") renderAchievements(achievementsList);
  }
}

// ─── Авторизация (ТОЛЬКО через бэкенд, без mock-fallback) ───────────────────
// [FIX-1] Убран mockApiFallback для auth — больше нельзя войти под любым логином
async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("authLoginInput").value.trim();
  const password = document.getElementById("authPasswordInput").value;

  if (!username || !password) {
    showToast(currentLang === "RU" ? "Заполните все поля." : "Please fill in all fields.");
    return;
  }

  if (currentAuthMode === "register") {
    const passConfirm = document.getElementById("authPasswordConfirmInput").value;
    if (password !== passConfirm) {
      showToast(currentLang === "RU" ? "Пароли не совпадают!" : "Passwords do not match!");
      return;
    }
  }

  const btn = document.getElementById("authSubmitBtn");
  const originalText = btn ? btn.textContent : "";
  if (btn) { btn.disabled = true; btn.textContent = "..."; }

  try {
    let data;
    if (currentAuthMode === "login") {
      // [FIX-1] Прямой fetch без mockApiFallback — реальный бэкенд
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
      if (!email) {
        showToast("Введите email.");
        return;
      }
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

    localStorage.setItem("username", data.username);
    isUserLoggedIn = true;
    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = data.username;
    toggleAuthModal();
    setTimeout(() => {
      toggleProfile();
      loadProfileData();
    }, 300);

  } catch (err) {
    showToast(err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = originalText; }
  }
}

// ─── Выход ───────────────────────────────────────────────────────────────────
function handleLogout() {
  fetch(API_BASE + "/api/auth/logout", { method: "POST", credentials: "include" }).catch(() => {});

  isUserLoggedIn = false;
  localStorage.removeItem("username");

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = "Войти";

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl) {
    avatarEl.src = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80";
  }

  document.getElementById("sideProfile")?.classList.remove("open");
  showToast(currentLang === "RU" ? "Вы вышли из аккаунта." : "You have been logged out.");
}

// ─── VK OAuth [FIX-3] — Client ID с бэкенда + state ─────────────────────────
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

    const redirectUri = encodeURIComponent(window.location.origin + "/index.html");
    const url = `https://id.vk.com/authorize`
      + `?response_type=code`
      + `&client_id=${client_id}`
      + `&redirect_uri=${redirectUri}`
      + `&scope=email`
      + `&state=${encodeURIComponent(state)}`;

    window.location.href = url;
  } catch (err) {
    console.error("Ошибка VK OAuth:", err);
    showToast("Не удалось подключиться к серверу.");
  }
}

// ─── Google OAuth ─────────────────────────────────────────────────────────────
async function loginWithGoogle() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/google/client-id`);
    if (!res.ok) {
      showToast("Google OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    const state = crypto.randomUUID();
    sessionStorage.setItem("oauth_state", state);
    sessionStorage.setItem("oauth_provider", "google");

    const REDIRECT_URI = window.location.origin + "/index.html";
    const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    url.searchParams.set("client_id", client_id);
    url.searchParams.set("redirect_uri", REDIRECT_URI);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", "openid email profile");
    url.searchParams.set("access_type", "online");
    url.searchParams.set("state", state);

    window.location.href = url.toString();
  } catch (err) {
    console.error("Ошибка Google OAuth:", err);
    showToast("Не удалось подключиться к серверу.");
  }
}

// ─── Google OAuth callback (с проверкой state) ───────────────────────────────
async function handleGoogleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code   = params.get("code");
  const state  = params.get("state");
  const error  = params.get("error");
  const provider = sessionStorage.getItem("oauth_provider") || "google";

  if (!code && !error) return;

  window.history.replaceState({}, "", window.location.pathname);

  if (error) {
    showToast("Ошибка входа: " + error);
    return;
  }

  // [FIX-4] Проверка state
  const savedState = sessionStorage.getItem("oauth_state");
  sessionStorage.removeItem("oauth_state");
  sessionStorage.removeItem("oauth_provider");

  if (!state || state !== savedState) {
    showToast("Ошибка безопасности OAuth. Попробуйте снова.");
    return;
  }

  const endpoint = provider === "vk"
    ? `/api/auth/vk/callback?code=${encodeURIComponent(code)}`
    : `/api/auth/google/callback?code=${encodeURIComponent(code)}`;

  try {
    const res = await fetch(API_BASE + endpoint, { credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast("Ошибка авторизации: " + (err.detail || "неизвестная ошибка"));
      return;
    }

    const data = await res.json();
    localStorage.setItem("username", data.username);
    isUserLoggedIn = true;

    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = data.username;

    const authModal = document.getElementById("authModal");
    if (authModal) authModal.classList.remove("open");

    setTimeout(() => {
      if (typeof toggleProfile === "function") toggleProfile();
      loadProfileData();
    }, 300);

  } catch (err) {
    console.error("OAuth callback error:", err);
    showToast("Не удалось подключиться к серверу.");
  }
}

// ─── Аватар с компьютера ─────────────────────────────────────────────────────
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
    // В продакшне: загружать на CDN и отправлять URL на /api/profile/avatar
  };
  reader.readAsDataURL(file);
}

// ─── Обновление никнейма через API ──────────────────────────────────────────
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
    // Откатить UI
    const nameEl = document.getElementById("profileName");
    const saved = localStorage.getItem("username");
    if (nameEl && saved) nameEl.textContent = saved;
  }
}
