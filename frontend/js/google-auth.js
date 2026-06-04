const REDIRECT_URI = window.location.origin + "/index.html";
const BACKEND_URL = "https://lotus-tur-production.up.railway.app";

async function loginWithGoogle() {
  const res = await fetch("https:lotus-tur-production-23c6.up.railway.app");
  const { client_id } = await res.json();

  const redirectUri = encodeURIComponent(window.location.origin + "/index.html");
  const scope = encodeURIComponent("email profile");
  const url = `https://accounts.google.com/o/oauth2/v2/auth`
    + `?client_id=${client_id}`
    + `&redirect_uri=${redirectUri}`
    + `&response_type=code`
    + `&scope=${scope}`;

  window.location.href = url;
}

  const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", REDIRECT_URI);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid email profile");
  url.searchParams.set("access_type", "online");
  window.location.href = url.toString();

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
