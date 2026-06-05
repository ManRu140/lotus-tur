const REDIRECT_URI = window.location.origin + "/index.html";
const BACKEND_URL = "https://lotus-tur-production-23c6.up.railway.app";

async function loginWithGoogle() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/google/client-id`);
    if (!res.ok) {
      alert("Google OAuth не настроен на сервере.");
      return;
    }
    const { client_id } = await res.json();

    const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    url.searchParams.set("client_id", client_id);
    url.searchParams.set("redirect_uri", REDIRECT_URI);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", "openid email profile");
    url.searchParams.set("access_type", "online");
    window.location.href = url.toString();
  } catch (err) {
    console.error("Ошибка Google OAuth:", err);
    alert("Не удалось подключиться к серверу.");
  }
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
      { credentials: "include" },
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert("Ошибка авторизации: " + (err.detail || "неизвестная ошибка"));
      return;
    }

    const data = await res.json();

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
