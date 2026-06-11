const API_BASE = "https://lotus-tur-production-23c6.up.railway.app";

let isUserLoggedIn   = false;
let currentLang      = "RU";
let isGridViewActive = false;
let currentAuthMode  = "login";

let calYear         = 2026;
let calMonth        = 5;
let selectedDateStr = "";


function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const csrfToken = getCookie("csrf_token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    ...options.headers,
  };
  const res = await fetch(API_BASE + path, { ...options, headers, credentials: "include" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Ошибка ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}


async function checkExistingSession() {

  const savedToken  = localStorage.getItem("access_token");
  const savedName   = localStorage.getItem("username");
  const savedAvatar = localStorage.getItem("avatar_url");
  const savedFull   = localStorage.getItem("full_name");

  if (savedToken && savedName) {
    isUserLoggedIn = true;
    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = savedFull || savedName;
    const subEl = document.getElementById("profileSub");
    if (subEl) subEl.textContent = savedName;
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl && savedAvatar) avatarEl.src = savedAvatar;
  }

  if (!savedToken) return;


  try {
    const data = await apiFetch("/api/auth/me");
    if (data && data.username) {
      isUserLoggedIn = true;
      localStorage.setItem("username", data.username);
      if (data.avatar_url) localStorage.setItem("avatar_url", data.avatar_url);
      if (data.full_name)  localStorage.setItem("full_name",  data.full_name);

      const nameEl = document.getElementById("profileName");
      if (nameEl) nameEl.textContent = data.full_name || data.username;
      const subEl = document.getElementById("profileSub");
      if (subEl) subEl.textContent = data.username;
      const avatarEl = document.getElementById("profileAvatar");
      if (avatarEl && data.avatar_url) avatarEl.src = data.avatar_url;

      loadProfileData();
    }
  } catch {

    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    localStorage.removeItem("avatar_url");
    localStorage.removeItem("full_name");
    isUserLoggedIn = false;
  }
}


async function loadProfileData() {
  if (!isUserLoggedIn) return;

  try {
    const profile = await apiFetch("/api/profile/me");


    localStorage.setItem("username",   profile.username);
    if (profile.avatar_url) localStorage.setItem("avatar_url", profile.avatar_url);
    if (profile.full_name)  localStorage.setItem("full_name",  profile.full_name);


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

  } catch (e) {
    console.warn("Не удалось загрузить профиль:", e.message);
  }

  loadMyBookings();
  loadMyAchievements();
}


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


async function loadMyAchievements() {
  try {
    const achievements = await apiFetch("/api/profile/achievements");
    renderAchievements(achievements);
  } catch (e) {
    console.warn("Не удалось загрузить достижения:", e.message);
    if (typeof achievementsList !== "undefined") renderAchievements(achievementsList);
  }
}


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

    _applyLoginData(data);
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


function _applyLoginData(data) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("username", data.username);
  if (data.avatar_url) localStorage.setItem("avatar_url", data.avatar_url);
  if (data.full_name)  localStorage.setItem("full_name",  data.full_name);

  isUserLoggedIn = true;

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = data.full_name || data.username;

  const subEl = document.getElementById("profileSub");
  if (subEl) subEl.textContent = data.username;

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl && data.avatar_url) avatarEl.src = data.avatar_url;
}


function handleLogout() {
  fetch(API_BASE + "/api/auth/logout", { method: "POST", credentials: "include" }).catch(() => {});

  isUserLoggedIn = false;
  localStorage.removeItem("access_token");
  localStorage.removeItem("username");
  localStorage.removeItem("avatar_url");
  localStorage.removeItem("full_name");

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = "Войти";

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl) {
    avatarEl.src = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80";
  }

  document.getElementById("sideProfile")?.classList.remove("open");
  showToast(currentLang === "RU" ? "Вы вышли из аккаунта." : "You have been logged out.");
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
    console.error("Ошибка Google OAuth:", err);
    showToast("Не удалось подключиться к серверу.");
  }
}


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

    const uriParam = redirectUri ? `&redirect_uri=${encodeURIComponent(redirectUri)}` : "";
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
    console.error("OAuth callback error:", err);
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
