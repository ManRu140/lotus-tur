/**
 * app.js — ИСПРАВЛЕННЫЕ ФРАГМЕНТЫ (критичные правки)
 *
 * [FIX-1] Убраны localStorage.setItem/getItem для JWT-токена — XSS-уязвимость.
 *         Аутентификация теперь только через HttpOnly Cookie (устанавливается бэкендом).
 * [FIX-2] Добавлен state параметр в OAuth-флоу (CSRF/OAuth hijacking защита).
 * [FIX-3] Исправлен двойной FileReader в loadAvatarFromPC.
 * [FIX-4] Убрано хранение base64-аватара в localStorage (квота ~5MB, QuotaExceededError).
 * [FIX-5] Объединены API_URL и BACKEND_URL в одну константу.
 * [FIX-6] Исправлен loginWithVK — Client ID получается с бэкенда, добавлен state.
 */

// ─── [FIX-5] Единственная точка конфигурации URL бэкенда ────────────────────
const API_BASE = "https://lotus-tur-production-23c6.up.railway.app";

// Состояние приложения — БЕЗ authToken (токен хранится в HttpOnly Cookie)
// [FIX-1] Убраны: const authToken = localStorage.getItem("token")
let isUserLoggedIn   = false;
let currentLang      = "RU";
let isGridViewActive = false;
let currentAuthMode  = "login";

let calYear         = 2026;
let calMonth        = 5;
let selectedDateStr = "";

let cachedToursData = [];

// При загрузке проверяем сессию через /api/auth/me (Cookie отправляется автоматически)
async function checkExistingSession() {
  try {
    const data = await apiFetch("/api/auth/me");
    if (data && data.username) {
      isUserLoggedIn = true;
      const el = document.getElementById("profileName");
      if (el) el.textContent = data.username;
      // [FIX-1] Сохраняем только несекретное имя пользователя
      localStorage.setItem("username", data.username);
    }
  } catch {
    // Нет активной сессии — ок
  }
}

// ─── [FIX-1] Универсальный API-хелпер БЕЗ Authorization header ──────────────
// Cookie отправляется автоматически благодаря credentials: "include"
async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  // [FIX-1] Убрана строка: if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  try {
    const res = await fetch(API_BASE + path, { ...options, headers, credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка ${res.status}`);
    }
    return res.status === 204 ? null : res.json();
  } catch (e) {
    console.warn("API недоступен, используем локальные данные.", e);
    return mockApiFallback(path, options);
  }
}

// ─── [FIX-1] handleAuthSubmit — убрано сохранение токена в localStorage ─────
async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("authLoginInput").value.trim();
  const password = document.getElementById("authPasswordInput").value;

  if (!username || !password) {
    alert(currentLang === "RU" ? "Заполните все поля." : "Please fill in all fields.");
    return;
  }

  if (currentAuthMode === "register") {
    const passConfirm = document.getElementById("authPasswordConfirmInput").value;
    if (password !== passConfirm) {
      alert(currentLang === "RU" ? "Пароли не совпадают!" : "Passwords do not match!");
      return;
    }
  }

  const btn = document.getElementById("authSubmitBtn");
  if (btn) btn.disabled = true;

  try {
    let data;
    if (currentAuthMode === "login") {
      data = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
    } else {
      const email = document.getElementById("authEmailInput").value.trim();
      data = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, email, password }),
      });
    }

    // [FIX-1] Убраны: localStorage.setItem("token", ...) и authToken = data.access_token
    // HttpOnly Cookie установлена бэкендом автоматически
    localStorage.setItem("username", data.username); // несекретные данные — ок
    isUserLoggedIn = true;
    document.getElementById("profileName").textContent = data.username;
    toggleAuthModal();
    setTimeout(toggleProfile, 300);
  } catch (err) {
    alert(err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ─── [FIX-1] handleLogout — убрано удаление токена из localStorage ───────────
function handleLogout() {
  // Очищаем HttpOnly Cookie на бэкенде
  apiFetch("/api/auth/logout", { method: "POST" }).catch(() => {});

  // [FIX-1] Убраны: authToken = null; localStorage.removeItem("token");
  isUserLoggedIn = false;
  localStorage.removeItem("username");
  localStorage.removeItem("my_bookings");

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = "Приморский_Странник";

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl) {
    avatarEl.src = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80";
  }

  document.getElementById("sideProfile").classList.remove("open");
  alert(currentLang === "RU" ? "Вы вышли из аккаунта." : "You have been logged out.");
}

// ─── [FIX-2] loginWithVK — state параметр + Client ID с бэкенда ─────────────
async function loginWithVK() {
  try {
    // Получаем VK Client ID с бэкенда (аналогично Google)
    const res = await fetch(`${API_BASE}/api/auth/vk/client-id`);
    if (!res.ok) {
      alert("VK OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    // [FIX-2] Генерируем случайный state для защиты от CSRF/OAuth hijacking
    const state = crypto.randomUUID();
    sessionStorage.setItem("oauth_state", state);
    sessionStorage.setItem("oauth_provider", "vk");

    const redirectUri = encodeURIComponent(window.location.origin + "/index.html");
    const url = `https://id.vk.com/authorize`
      + `?response_type=code`
      + `&client_id=${client_id}`
      + `&redirect_uri=${redirectUri}`
      + `&scope=email`
      + `&state=${encodeURIComponent(state)}`;  // [FIX-2] state обязателен

    window.location.href = url;
  } catch (err) {
    console.error("Ошибка VK OAuth:", err);
    alert("Не удалось подключиться к серверу.");
  }
}

// ─── [FIX-2] loginWithGoogle — добавлен state параметр ──────────────────────
async function loginWithGoogle() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/google/client-id`);
    if (!res.ok) {
      alert("Google OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    // [FIX-2] Генерируем state для защиты от CSRF/OAuth hijacking
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
    url.searchParams.set("state", state);  // [FIX-2] state обязателен

    window.location.href = url.toString();
  } catch (err) {
    console.error("Ошибка Google OAuth:", err);
    alert("Не удалось подключиться к серверу.");
  }
}

// ─── [FIX-2] handleGoogleCallback — проверка state ──────────────────────────
async function handleGoogleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code   = params.get("code");
  const state  = params.get("state");
  const error  = params.get("error");

  window.history.replaceState({}, "", window.location.pathname);

  if (error) {
    console.error("Google ошибка:", error);
    alert("Ошибка входа через Google: " + error);
    return;
  }

  if (!code) return;

  // [FIX-2] Проверяем state — защита от CSRF
  const savedState = sessionStorage.getItem("oauth_state");
  sessionStorage.removeItem("oauth_state");
  sessionStorage.removeItem("oauth_provider");

  if (!state || state !== savedState) {
    alert("Ошибка безопасности OAuth: недействительный state. Попробуйте снова.");
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/api/auth/google/callback?code=${encodeURIComponent(code)}`,
      { credentials: "include" },
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert("Ошибка авторизации: " + (err.detail || "неизвестная ошибка"));
      return;
    }

    const data = await res.json();

    // [FIX-1] Убраны: localStorage.setItem("token", ...) и authToken = ...
    localStorage.setItem("username", data.username);

    isUserLoggedIn = true;

    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = data.username;

    const authModal = document.getElementById("authModal");
    if (authModal) authModal.classList.remove("open");

    setTimeout(() => {
      if (typeof toggleProfile === "function") toggleProfile();
    }, 300);
  } catch (err) {
    console.error("Ошибка запроса:", err);
    alert("Не удалось подключиться к серверу.");
  }
}

// ─── [FIX-3, FIX-4] loadAvatarFromPC — один FileReader, нет localStorage ────
async function loadAvatarFromPC(input) {
  if (!input.files || !input.files[0]) return;

  const file = input.files[0];

  const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
  if (!allowedTypes.includes(file.type)) {
    alert("Допустимые форматы: JPEG, PNG, WEBP, GIF");
    return;
  }
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    alert("Файл слишком большой. Максимальный размер: 5MB");
    return;
  }

  // [FIX-3] Один FileReader для обоих задач (превью и сохранение)
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;

    // Немедленное превью
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl) avatarEl.src = dataUrl;

    // [FIX-4] НЕ сохраняем base64 в localStorage — это вызывает QuotaExceededError
    // В production: загружать файл на CDN через presigned URL
    // Для dev: хранить только в памяти (avatarDataUrl переменная)
    // localStorage.setItem("avatar_preview", dataUrl); // ← УБРАНО
  };
  reader.readAsDataURL(file);
}
