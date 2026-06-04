const API_URL = "https://lotus-tur-production-23c6.up.railway.app";

// Токен из URL после OAuth-редиректа
const _urlParams = new URLSearchParams(window.location.search);
const _urlToken  = _urlParams.get("token");
if (_urlToken) {
  localStorage.setItem("token", _urlToken);
  window.history.replaceState({}, "", window.location.pathname);
}

// Состояние приложения
let isUserLoggedIn   = false;
let currentLang      = "RU";
let isGridViewActive = false;
let currentAuthMode  = "login";
let authToken        = localStorage.getItem("token") || null;

let calYear         = 2026;
let calMonth        = 5;
let selectedDateStr = "";

// Кэш туров для доступа в календаре
let cachedToursData = [];

if (authToken) {
  isUserLoggedIn = true;
  const savedName = localStorage.getItem("username");
  if (savedName) {
    const el = document.getElementById("profileName");
    if (el) el.textContent = savedName;
  }
}

// Универсальный API-хелпер с fallback на локальные данные
async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  try {
    const res = await fetch(API_URL + path, { ...options, headers, credentials: "include" });
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

// Локальный фоллбек для работы без сервера
function mockApiFallback(path, options) {
  if (path === "/api/tours") {
    return Promise.resolve(toursData);
  }
  if (path === "/api/bookings" && options.method === "POST") {
    return Promise.reject(new Error("Сервер недоступен. Бронирование невозможно."));
  }
  if (path === "/api/bookings/my") {
    let bookings = JSON.parse(localStorage.getItem("my_bookings") || "[]");
    if (!bookings.length) {
      bookings = [
        { id: 1, tour_name: "Остров Аскольд: Тайны Маяка",  tour_date: "2026-06-12", people_count: 2, status: "booked"   },
        { id: 2, tour_name: "Бухта Триозерье: Белые Пески", tour_date: "2026-06-05", people_count: 1, status: "started"  },
      ];
      localStorage.setItem("my_bookings", JSON.stringify(bookings));
    }
    return Promise.resolve(bookings);
  }
  if (path === "/api/profile/achievements") {
    return Promise.resolve(achievementsList);
  }
  if (path === "/api/auth/login" || path === "/api/auth/register") {
    return Promise.reject(new Error("Сервер недоступен. Попробуйте позже."));
  }
  if (path === "/api/promo/ref") {
    return Promise.resolve({ link: "https://poravpohod.ru/ref?id=43219" });
  }
  if (path === "/api/promo/apply") {
    return Promise.resolve({ message: "Промокод успешно применен!" });
  }
  return Promise.resolve({});
}

// ── ТУРЫ ─────────────────────────────────────────────────────────────────────

async function renderToursGrid() {
  const container = document.getElementById("toursContainer");
  if (!container) return;

  let tours = [];
  try {
    tours = await apiFetch("/api/tours");
  } catch {
    tours = toursData;
  }

  if (tours && tours.length) cachedToursData = tours;

  container.innerHTML = "";
  const btnText = currentLang === "RU" ? "Купить" : "Buy Ticket";

  tours.forEach((tour) => {
    const img   = tour.img_url || tour.img || "";
    const desc  = tour.description || tour.desc || "";
    const name  = tour.name || "";
    const price = tour.price
      ? typeof tour.price === "number"
        ? tour.price.toLocaleString("ru-RU")
        : tour.price
      : "";

    // Создаём карточку через DOM API (XSS-безопасно)
    const card = document.createElement("div");
    card.className = "tour-card";

    const imgDiv = document.createElement("div");
    imgDiv.className = "tour-img-placeholder";
    imgDiv.style.backgroundImage = `url('${img}')`;

    const staticTitle = document.createElement("div");
    staticTitle.className = "tour-static-title";
    const h3static = document.createElement("h3");
    h3static.className = "tour-name";
    h3static.textContent = name;
    staticTitle.appendChild(h3static);

    const hoverInfo = document.createElement("div");
    hoverInfo.className = "tour-hover-info";

    const tagSpan = document.createElement("span");
    tagSpan.className = "tour-tag";
    tagSpan.textContent = tour.tag || "";

    const h3hover = document.createElement("h3");
    h3hover.className = "tour-name";
    h3hover.textContent = name;

    const descP = document.createElement("p");
    descP.className = "tour-desc";
    descP.textContent = desc;

    const metaDiv = document.createElement("div");
    metaDiv.className = "tour-meta";

    const priceDiv = document.createElement("div");
    priceDiv.className = "tour-price";
    priceDiv.textContent = price + " ";
    const rubleSpan = document.createElement("span");
    rubleSpan.textContent = "₽";
    priceDiv.appendChild(rubleSpan);

    const btn = document.createElement("button");
    btn.className = "tour-btn";
    btn.dataset.tourId = tour.id;
    btn.textContent = btnText;
    btn.addEventListener("click", () => openBookingWithTour(tour.id));

    metaDiv.appendChild(priceDiv);
    metaDiv.appendChild(btn);

    hoverInfo.appendChild(tagSpan);
    hoverInfo.appendChild(h3hover);
    hoverInfo.appendChild(descP);
    hoverInfo.appendChild(metaDiv);

    card.appendChild(imgDiv);
    card.appendChild(staticTitle);
    card.appendChild(hoverInfo);

    container.appendChild(card);
  });

  updateBtnAllText();
  populateTourSelectOptions(tours);
}

function populateTourSelectOptions(tours) {
  const select = document.getElementById("bookTourSelect");
  if (!select) return;
  select.innerHTML = "";
  const defaultOpt = document.createElement("option");
  defaultOpt.value = "";
  defaultOpt.textContent = currentLang === "RU" ? "Выберите тур..." : "Select a tour...";
  select.appendChild(defaultOpt);
  (tours || toursData).forEach((tour) => {
    const opt = document.createElement("option");
    opt.value = tour.id;
    opt.textContent = tour.name;
    select.appendChild(opt);
  });
}

function toggleToursDisplayView() {
  const container = document.getElementById("toursContainer");
  isGridViewActive = !isGridViewActive;
  container.classList.toggle("view-all-cards", isGridViewActive);
  updateBtnAllText();
}

function updateBtnAllText() {
  const btnSpan = document.getElementById("txtBtnAll");
  if (!btnSpan) return;
  btnSpan.textContent = isGridViewActive
    ? currentLang === "RU" ? "Свернуть" : "Collapse"
    : currentLang === "RU" ? "Все туры" : "All tours";
}

// ── БРОНИРОВАНИЕ И КАЛЕНДАРЬ ─────────────────────────────────────────────────

function toggleBookingModal() {
  document.getElementById("bookingModal").classList.toggle("open");
}

function openBookingGeneral() {
  if (!isUserLoggedIn) { toggleAuthModal(); return; }
  const select = document.getElementById("bookTourSelect");
  if (select) { select.value = ""; select.disabled = false; }
  selectedDateStr = "";
  initCalendarForCurrentSelection();
  toggleBookingModal();
}

function openBookingWithTour(tourId) {
  if (!isUserLoggedIn) { toggleAuthModal(); return; }
  const select = document.getElementById("bookTourSelect");
  if (select) { select.value = tourId; select.disabled = false; }
  selectedDateStr = "";
  initCalendarForCurrentSelection();
  toggleBookingModal();
}

function initCalendarForCurrentSelection() {
  const select = document.getElementById("bookTourSelect");
  if (!select) return;
  // Вешаем обработчик один раз
  if (!select.dataset.listenerAdded) {
    select.addEventListener("change", () => {
      selectedDateStr = "";
      const hiddenDateInput = document.getElementById("bookDateInput");
      if (hiddenDateInput) hiddenDateInput.value = "";
      renderMiniCalendar(calYear, calMonth);
    });
    select.dataset.listenerAdded = "true";
  }
  renderMiniCalendar(calYear, calMonth);
}

function renderMiniCalendar(year, month) {
  const placeholder = document.getElementById("miniCalendarPlaceholder");
  if (!placeholder) return;

  const select = document.getElementById("bookTourSelect");
  const selectedTourId = select ? select.value : "";

  // Используем кэш API, иначе локальные данные
  const allTours = cachedToursData.length ? cachedToursData : toursData;
  const selectedTour = allTours.find((t) => t.id === selectedTourId);

  // API возвращает booked_dates, локальные данные — bookedDates
  const tourBookedDates = selectedTour
    ? (selectedTour.booked_dates || selectedTour.bookedDates || [])
    : [];

  const monthsRu = ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"];
  const monthsEn = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const currentMonthName = currentLang === "RU" ? monthsRu[month] : monthsEn[month];

  const weekRu = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"];
  const weekEn = ["Mo","Tu","We","Th","Fr","Sa","Su"];
  const weekdaysHtml = (currentLang === "RU" ? weekRu : weekEn)
    .map((d) => `<div>${d}</div>`).join("");

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const firstDayIndex = (new Date(year, month, 1).getDay() + 6) % 7;
  const totalDays     = new Date(year, month + 1, 0).getDate();

  let daysHtml = "";
  for (let i = 0; i < firstDayIndex; i++) {
    daysHtml += `<div class="cal-day empty-day"></div>`;
  }
  for (let dayNum = 1; dayNum <= totalDays; dayNum++) {
    const mm = String(month + 1).padStart(2, "0");
    const dd = String(dayNum).padStart(2, "0");
    const dateString = `${year}-${mm}-${dd}`;

    const dayDate = new Date(year, month, dayNum);
    const isPast      = dayDate < today;
    const isBookedOut = !isPast && select?.value ? tourBookedDates.includes(dateString) : false;

    let statusClass;
    if (isPast) statusClass = "past-day";
    else if (isBookedOut) statusClass = "booked-out";
    else if (selectedDateStr === dateString) statusClass = "selected";
    else statusClass = "available";

    daysHtml += `
      <div class="cal-day ${statusClass}"
           data-date="${dateString}"
           data-booked="${isBookedOut}"
           data-past="${isPast}">
        ${dayNum}
      </div>
    `;
  }

  const titleText = currentLang === "RU" ? "Выберите дату тура" : "Choose your tour date";

  placeholder.innerHTML = `
    <label class="form-group-block"
      style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-light-main);display:block;margin-bottom:6px;">
      ${titleText}
    </label>
    <div class="mini-calendar-container">
      <div class="calendar-header">
        <button type="button" class="calendar-nav-btn" id="calPrevBtn">&lsaquo;</button>
        <div class="calendar-month-year">${currentMonthName} ${year}</div>
        <button type="button" class="calendar-nav-btn" id="calNextBtn">&rsaquo;</button>
      </div>
      <div class="calendar-weekdays">${weekdaysHtml}</div>
      <div class="calendar-days-grid" id="calDaysGrid">${daysHtml}</div>
    </div>
    <input type="hidden" name="tour_date" id="bookDateInput" value="${selectedDateStr}">
  `;

  document.getElementById("calPrevBtn").addEventListener("click", prevCalendarMonth);
  document.getElementById("calNextBtn").addEventListener("click", nextCalendarMonth);
  document.getElementById("calDaysGrid").addEventListener("click", (e) => {
    const day = e.target.closest(".cal-day");
    if (!day || day.classList.contains("empty-day")) return;
    selectCalendarDate(day.dataset.date, day.dataset.booked === "true", day.dataset.past === "true");
  });
}

function prevCalendarMonth() {
  calMonth--;
  if (calMonth < 0) { calMonth = 11; calYear--; }
  renderMiniCalendar(calYear, calMonth);
}

function nextCalendarMonth() {
  calMonth++;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  renderMiniCalendar(calYear, calMonth);
}

function selectCalendarDate(dateStr, isBookedOut, isPast) {
  if (isPast) {
    alert(currentLang === "RU"
      ? "Нельзя бронировать прошедшую дату!"
      : "Cannot book a past date!");
    return;
  }
  if (isBookedOut) {
    alert(currentLang === "RU"
      ? "Эта дата полностью занята! На неё нет свободных мест."
      : "This date is fully booked out!");
    return;
  }
  const select = document.getElementById("bookTourSelect");
  if (select && !select.value) {
    alert(currentLang === "RU"
      ? "Пожалуйста, сначала выберите направление!"
      : "Please select a tour first!");
    return;
  }
  selectedDateStr = dateStr;
  const hiddenInput = document.getElementById("bookDateInput");
  if (hiddenInput) hiddenInput.value = dateStr;
  renderMiniCalendar(calYear, calMonth);
}

async function handleBookingSubmit(e) {
  e.preventDefault();
  const tourId  = document.getElementById("bookTourSelect").value;
  const dateVal = document.getElementById("bookDateInput")?.value;

  if (!tourId) {
    alert(currentLang === "RU" ? "Пожалуйста, выберите направление!" : "Please select a tour!"); return;
  }
  if (!dateVal) {
    alert(currentLang === "RU" ? "Пожалуйста, выберите свободную дату на календаре!" : "Please select an available date!"); return;
  }

  const peopleCountEl = document.getElementById("bookPeopleCount");
  const peopleCount = peopleCountEl ? parseInt(peopleCountEl.value, 10) || 1 : 1;

  const payload = {
    tour_id:      tourId,
    first_name:   document.getElementById("bookName").value,
    phone:        document.getElementById("bookPhone").value,
    email:        document.getElementById("bookEmail").value,
    tour_date:    dateVal,
    preferred_time: document.getElementById("bookTime")?.value || null,
    people_count: peopleCount,
    comment:      document.getElementById("bookMessage")?.value || "",
  };

  const btn = document.getElementById("bookSubmitBtn");
  if (btn) { btn.disabled = true; btn.textContent = "Отправляем..."; }

  try {
    await apiFetch("/api/bookings", { method: "POST", body: JSON.stringify(payload) });
    alert(currentLang === "RU"
      ? `Заявка успешно отправлена на ${dateVal}! Ждите звонка.`
      : `Booking sent for ${dateVal}! We will contact you shortly.`);
    toggleBookingModal();
    e.target.reset();
    selectedDateStr = "";
    renderMyBookings();
  } catch (err) {
    alert(err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Подтвердить заказ"; }
  }
}

// ── АВТОРИЗАЦИЯ ───────────────────────────────────────────────────────────────

function toggleAuthModal() {
  document.getElementById("authModal").classList.toggle("open");
}

function switchAuthMode(mode) {
  currentAuthMode = mode;
  const form         = document.getElementById("authMainForm");
  const tabLogin     = document.getElementById("tabLoginBtn");
  const tabRegister  = document.getElementById("tabRegisterBtn");
  const submitBtn    = document.getElementById("authSubmitBtn");

  form.classList.toggle("auth-mode-register", mode === "register");

  tabLogin.classList.toggle("active",    mode === "login");
  tabLogin.setAttribute("aria-selected", mode === "login");
  tabRegister.classList.toggle("active", mode === "register");
  tabRegister.setAttribute("aria-selected", mode === "register");

  const emailInput  = document.getElementById("authEmailInput");
  const passConfirm = document.getElementById("authPasswordConfirmInput");

  if (mode === "login") {
    emailInput.removeAttribute("required");
    passConfirm.removeAttribute("required");
    submitBtn.textContent = currentLang === "RU" ? "Войти" : "Login";
  } else {
    emailInput.setAttribute("required", "true");
    passConfirm.setAttribute("required", "true");
    submitBtn.textContent = currentLang === "RU" ? "Зарегистрироваться" : "Register";
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("authLoginInput").value.trim();
  const password = document.getElementById("authPasswordInput").value;

  if (!username || !password) {
    alert(currentLang === "RU" ? "Заполните все поля." : "Please fill in all fields."); return;
  }

  if (currentAuthMode === "register") {
    const passConfirm = document.getElementById("authPasswordConfirmInput").value;
    if (password !== passConfirm) {
      alert(currentLang === "RU" ? "Пароли не совпадают!" : "Passwords do not match!"); return;
    }
  }

  const btn = document.getElementById("authSubmitBtn");
  if (btn) btn.disabled = true;

  try {
    let data;
    if (currentAuthMode === "login") {
      data = await apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
    } else {
      const email = document.getElementById("authEmailInput").value.trim();
      data = await apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify({ username, email, password }) });
    }

    authToken = data.access_token;
    localStorage.setItem("token",    authToken);
    localStorage.setItem("username", data.username);

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

function handleProfileClick() {
  if (isUserLoggedIn) toggleProfile();
  else toggleAuthModal();
}

function handleFakeSocialLogin() {
  alert("OAuth пока не подключён. Используйте обычный вход.");
}

// ── ЛИЧНЫЙ КАБИНЕТ ────────────────────────────────────────────────────────────

function toggleProfile() {
  const sideProfile = document.getElementById("sideProfile");
  sideProfile.classList.toggle("open");
  if (sideProfile.classList.contains("open")) {
    renderAchievements();
    renderMyBookings();
    loadRefLink();
  }
}

function handleLogout() {
  // Очищаем HttpOnly cookie на бэкенде
  apiFetch("/api/auth/logout", { method: "POST" }).catch(() => {});

  authToken      = null;
  isUserLoggedIn = false;
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("my_bookings");

  const nameEl = document.getElementById("profileName");
  if (nameEl) nameEl.textContent = "Приморский_Странник";

  const avatarEl = document.getElementById("profileAvatar");
  if (avatarEl) avatarEl.src = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80";

  document.getElementById("sideProfile").classList.remove("open");
  alert(currentLang === "RU" ? "Вы вышли из аккаунта." : "You have been logged out.");
}

function switchProfileTab(index) {
  document.querySelectorAll(".p-tab-btn").forEach((b, i) => {
    b.classList.toggle("active", i === index);
    b.setAttribute("aria-selected", i === index);
  });
  document.querySelectorAll(".profile-tab-content").forEach((c, i) => {
    c.classList.toggle("active", i === index);
  });
}

function filterTours(status, targetEl) {
  document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
  if (targetEl) targetEl.classList.add("active");

  document.querySelectorAll(".p-tour-card").forEach((card) => {
    const visible = status === "all" || card.dataset.status === status;
    card.classList.toggle("hidden", !visible);
  });
}

async function renderMyBookings() {
  const container = document.getElementById("toursList");
  if (!container || !isUserLoggedIn) return;

  try {
    const bookings = await apiFetch("/api/bookings/my");
    container.innerHTML = "";

    if (!bookings.length) {
      container.innerHTML = '<p style="color:var(--text-light-muted);font-size:0.85rem">Бронирований пока нет.</p>';
      return;
    }

    const statusMap = {
      booked:    { label: "Забронировано", cls: "status-booked"    },
      started:   { label: "В пути",        cls: "status-started"   },
      completed: { label: "Завершен",       cls: "status-completed" },
      cancelled: { label: "Отменен",        cls: "status-cancelled" },
    };

    bookings.forEach((b) => {
      const s = statusMap[b.status] || { label: b.status, cls: "" };
      const card = document.createElement("div");
      card.className = "p-tour-card";
      card.dataset.status = b.status;

      const h4 = document.createElement("h4");
      h4.textContent = b.tour_name;

      const p = document.createElement("p");
      // Ручной парсинг даты — избегает off-by-one из-за UTC
      const [y, m, d] = b.tour_date.split("-").map(Number);
      const localDate = new Date(y, m - 1, d);
      p.textContent = `${localDate.toLocaleDateString("ru-RU")} · ${b.people_count} чел.`;

      const statusSpan = document.createElement("span");
      statusSpan.className = `tour-status ${s.cls}`;
      statusSpan.textContent = s.label;

      card.appendChild(h4);
      card.appendChild(p);
      card.appendChild(statusSpan);
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

async function renderAchievements() {
  const grid = document.getElementById("achGrid");
  if (!grid || !isUserLoggedIn) return;
  grid.innerHTML = "";

  const render = (list) =>
    list.forEach((ach) => {
      const card = document.createElement("div");
      card.className = `ach-card${ach.unlocked ? " unlocked" : ""}`;

      const iconDiv = document.createElement("div");
      iconDiv.className = "ach-icon";
      iconDiv.textContent = ach.icon;

      const infoDiv = document.createElement("div");
      infoDiv.className = "ach-info";

      const h5 = document.createElement("h5");
      h5.textContent = ach.title || ach.titleRu;

      const p = document.createElement("p");
      p.textContent = ach.description || ach.descRu;

      infoDiv.appendChild(h5);
      infoDiv.appendChild(p);
      card.appendChild(iconDiv);
      card.appendChild(infoDiv);
      grid.appendChild(card);
    });

  try {
    const achs = await apiFetch("/api/profile/achievements");
    render(achs);
  } catch {
    render(achievementsList);
  }
}

function enableInlineNicknameEdits() {
  const wrapper     = document.getElementById("nicknameWrapper");
  if (!wrapper) return;
  const currentName = document.getElementById("profileName").textContent;
  wrapper.innerHTML = `<input type="text" class="nickname-input" id="nicknameInput" maxlength="64">`;
  const input = document.getElementById("nicknameInput");
  input.value = currentName;
  input.focus();
  input.select();

  const save = async () => {
    const val = input.value.trim() || currentName;
    try {
      await apiFetch("/api/profile/username", { method: "PATCH", body: JSON.stringify({ username: val }) });
      localStorage.setItem("username", val);
    } catch { /* не критично */ }
    wrapper.innerHTML = `<h3 id="profileName" role="button" tabindex="0" aria-label="Нажмите для изменения имени"></h3>`;
    document.getElementById("profileName").textContent = val;
    document.getElementById("profileName").addEventListener("click", enableInlineNicknameEdits);
  };

  input.addEventListener("keydown", (e) => { if (e.key === "Enter") save(); });
  input.addEventListener("blur", save);
}

// Открывает диалог выбора файла для аватара
function openAvatarExplorer() {
  document.getElementById("avatarFileInput").click();
}

async function loadAvatarFromPC(input) {
  if (!input.files || !input.files[0]) return;

  const file = input.files[0];

  // Разрешённые типы и максимальный размер 5 МБ
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

  // Немедленное превью
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById("profileAvatar").src = e.target.result;
  };
  reader.readAsDataURL(file);

  // Сохраняем base64 локально (API в production требует cdn URL)
  try {
    const dataUrl = await new Promise((res) => {
      const r = new FileReader();
      r.onload = (e) => res(e.target.result);
      r.readAsDataURL(file);
    });
    localStorage.setItem("avatar_preview", dataUrl);
  } catch (e) {
    console.warn("Не удалось сохранить аватар:", e);
  }
}

// ── ПРОМОКОДЫ ─────────────────────────────────────────────────────────────────

async function loadRefLink() {
  const link = document.getElementById("refLink");
  if (!link || !isUserLoggedIn) return;
  try {
    const data = await apiFetch("/api/promo/ref");
    link.value = data.link;
  } catch { /* используем текущее значение */ }
}

async function copyRef() {
  const link = document.getElementById("refLink");
  try {
    await navigator.clipboard.writeText(link.value);
    alert(currentLang === "RU" ? "Ссылка скопирована!" : "Link copied!");
  } catch {
    // Fallback для браузеров без Clipboard API
    link.select();
    document.execCommand("copy");
    alert(currentLang === "RU" ? "Ссылка скопирована!" : "Link copied!");
  }
}

async function applyPromo() {
  const val = document.getElementById("promoInput").value.trim();
  if (!val) return;
  try {
    const data = await apiFetch("/api/promo/apply", { method: "POST", body: JSON.stringify({ code: val }) });
    alert(data.message);
  } catch (err) {
    alert(err.message);
  }
}

// ── ЯЗЫК ──────────────────────────────────────────────────────────────────────

function toggleLanguage() {
  currentLang = currentLang === "RU" ? "EN" : "RU";
  document.getElementById("langBtn").textContent = currentLang;
  const t = translations[currentLang];
  for (const id in t) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = t[id];
  }
  renderToursGrid();
  renderMiniCalendar(calYear, calMonth);
}

// ── НАВИГАЦИЯ: жидкий овал ────────────────────────────────────────────────────

function initNavFluidOval() {
  const oval    = document.getElementById("fluid-oval");
  const mainNav = document.getElementById("main-nav");
  if (!oval || !mainNav) return;

  document.querySelectorAll(".nav-target").forEach((target) => {
    target.addEventListener("mouseenter", () => {
      const tr = target.getBoundingClientRect();
      const cr = mainNav.getBoundingClientRect();
      oval.style.borderRadius = target.classList.contains("profile-btn") ? "50%" : "30px";
      oval.style.width  = `${tr.width}px`;
      oval.style.height = `${tr.height}px`;
      oval.style.left   = `${tr.left - cr.left}px`;
      oval.style.top    = `${tr.top - cr.top}px`;
      oval.style.opacity = "1";
    });
  });
  mainNav.addEventListener("mouseleave", () => { oval.style.opacity = "0"; });
}

// ── СМЕНА ТЕМЫ НАВБАРА ПРИ СКРОЛЛЕ ───────────────────────────────────────────

function initNavThemeObserver() {
  const mainNav = document.getElementById("main-nav");
  const trigger = document.querySelector(".trigger-light-theme");
  if (!mainNav || !trigger) return;

  new IntersectionObserver(
    (entries) => entries.forEach((e) => mainNav.classList.toggle("scrolled-light", e.isIntersecting)),
    { rootMargin: "-30px 0px -95% 0px", threshold: 0 }
  ).observe(trigger);
}

// ── БЕГУЩАЯ СТРОКА: пауза при наведении ──────────────────────────────────────

function initMarqueePause() {
  const wrapper = document.getElementById("marqueeWrapper");
  const line    = document.getElementById("marquee-line");
  if (!wrapper || !line) return;
  wrapper.addEventListener("mouseenter", () => { line.style.animationPlayState = "paused";  });
  wrapper.addEventListener("mouseleave", () => { line.style.animationPlayState = "running"; });
}

// ── ИНИЦИАЛИЗАЦИЯ ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  renderToursGrid();
  initNavFluidOval();
  initNavThemeObserver();
  initMarqueePause();

  // Восстанавливаем превью аватара из localStorage
  const savedAvatar = localStorage.getItem("avatar_preview");
  if (savedAvatar && isUserLoggedIn) {
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl) avatarEl.src = savedAvatar;
  }

  // Модальные окна
  document.getElementById("closeBookingBtn")
    ?.addEventListener("click", toggleBookingModal);
  document.getElementById("closeAuthBtn")
    ?.addEventListener("click", toggleAuthModal);
  document.getElementById("closeProfileBtn")
    ?.addEventListener("click", toggleProfile);

  // Закрытие по клику на фон
  document.getElementById("bookingModal")
    ?.addEventListener("click", (e) => { if (e.target === e.currentTarget) toggleBookingModal(); });
  document.getElementById("authModal")
    ?.addEventListener("click", (e) => { if (e.target === e.currentTarget) toggleAuthModal(); });

  // Закрытие по Escape
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const bm = document.getElementById("bookingModal");
    const am = document.getElementById("authModal");
    const sp = document.getElementById("sideProfile");
    if (bm?.classList.contains("open")) toggleBookingModal();
    else if (am?.classList.contains("open")) toggleAuthModal();
    else if (sp?.classList.contains("open")) toggleProfile();
  });

  // Формы
  document.getElementById("bookingForm")
    ?.addEventListener("submit", handleBookingSubmit);
  document.getElementById("authMainForm")
    ?.addEventListener("submit", handleAuthSubmit);

  // Вкладки авторизации
  document.querySelectorAll(".auth-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchAuthMode(btn.dataset.mode));
  });

  // Кнопки навбара
  document.getElementById("profileTrigger")
    ?.addEventListener("click", handleProfileClick);
  document.getElementById("langBtn")
    ?.addEventListener("click", toggleLanguage);
  document.getElementById("toggleGridBtn")
    ?.addEventListener("click", toggleToursDisplayView);

  // Кнопки с data-action="openBookingGeneral"
  document.querySelectorAll("[data-action='openBookingGeneral']").forEach((el) => {
    el.addEventListener("click", (e) => { e.preventDefault(); openBookingGeneral(); });
  });

  // Личный кабинет
  document.getElementById("logoutBtn")
    ?.addEventListener("click", handleLogout);

  document.querySelectorAll(".p-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchProfileTab(Number(btn.dataset.tab)));
  });

  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => filterTours(chip.dataset.filter, chip));
  });

  document.getElementById("avatarTrigger")
    ?.addEventListener("click", openAvatarExplorer);
  document.getElementById("avatarTrigger")
    ?.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") openAvatarExplorer(); });

  document.getElementById("profileName")
    ?.addEventListener("click", enableInlineNicknameEdits);

  document.getElementById("avatarFileInput")
    ?.addEventListener("change", function() { loadAvatarFromPC(this); });

  document.getElementById("btnCopy")
    ?.addEventListener("click", copyRef);
  document.getElementById("btnApply")
    ?.addEventListener("click", applyPromo);

  // Соцсети
  document.querySelectorAll(".social-btn[data-provider]").forEach((btn) => {
    btn.addEventListener("click", handleFakeSocialLogin);
  });
  document.getElementById("googleLoginBtn")
    ?.addEventListener("click", () => {
      if (typeof loginWithGoogle === "function") loginWithGoogle();
    });
});
