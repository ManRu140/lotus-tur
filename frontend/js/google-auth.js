// =============================================
// google-auth.js — Google OAuth для Лотос Тур
// =============================================

// BUG FIX #6: GOOGLE_CLIENT_ID убран из публичного JS-файла.
// Client ID должен читаться с бэкенда через /api/auth/google/client-id
// или встраиваться через шаблонизатор при деплое.
// Временно: если нужен срочный фикс — передавайте через window.__ENV__ в index.html.
// НИКОГДА не храните client_secret в браузере!

const REDIRECT_URI = window.location.origin + "/index.html";
const BACKEND_URL = "https://lotus-tur-production.up.railway.app";

async function loginWithGoogle() {
  // Получаем client_id с бэкенда (он не секретный, но лучше не в коде)
  let clientId = window.__GOOGLE_CLIENT_ID__;
  if (!clientId) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/google/client-id`);
      if (res.ok) {
        const data = await res.json();
        clientId = data.client_id;
      }
    } catch {
      // fallback: если эндпоинт не реализован, покажем ошибку
      alert("Вход через Google временно недоступен. Используйте обычный вход.");
      return;
    }
  }

  if (!clientId) {
    alert("Вход через Google не настроен.");
    return;
  }

  const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", REDIRECT_URI);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid email profile");
  url.searchParams.set("access_type", "online");
  window.location.href = url.toString();
}

async function handleGoogleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  const error = params.get("error");

  window.history.replaceState({}, "", window.location.pathname);

  if (error) {
    console.error("Google ошибка:", error);
    alert("Ошибка входа через Google: " + error);
    return;
  }

  if (!code) return;

  try {
    const res = await fetch(
      `${BACKEND_URL}/api/auth/google/callback?code=${encodeURIComponent(code)}`,
      { credentials: "include" }, // BUG FIX: нужно для получения HttpOnly cookies
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert("Ошибка авторизации: " + (err.detail || "неизвестная ошибка"));
      return;
    }

    const data = await res.json();

    // BUG FIX #1: единый ключ "token" (ранее использовался "token" в app.js,
    // но google-auth.js устанавливал "token" — теперь синхронизированы)
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", data.username);

    if (typeof authToken !== "undefined") authToken = data.access_token;
    if (typeof isUserLoggedIn !== "undefined") isUserLoggedIn = true;

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

if (new URLSearchParams(window.location.search).has("code")) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", handleGoogleCallback);
  } else {
    handleGoogleCallback();
  }
}
