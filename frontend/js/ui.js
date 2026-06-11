/**
 * ui.js — Модуль UI-логики
 *
 * Содержит:
 * - DOMContentLoaded инициализацию
 * - Навигацию и переключение кнопок
 * - Рендер карточек туров
 * - Модальное окно детали тура со слайдером
 * - Профиль: вкладки, фильтры туров, достижения, реферал
 * - Мини-календарь (общий для обеих форм)
 * - mockApiFallback для работы без бэкенда
 * - toggleProfile / toggleAuthModal (используются в app.js)
 */

// ── MOCK-ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (до подключения бэкенда) ──────────────────────
const mockUserTours = [
  {
    id: "askold",
    name: "Остров Аскольд",
    date: "2026-07-12",
    status: "booked",
    price: "7 500",
    img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80",
  },
  {
    id: "safari",
    name: "Морской Сафари-тур",
    date: "2026-06-08",
    status: "started",
    price: "9 500",
    img: "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=400&q=80",
  },
  {
    id: "sestra",
    name: "Гора Сестра",
    date: "2026-05-01",
    status: "completed",
    price: "6 000",
    img: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
  },
];

const tourSlides = {
  askold: [
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
  triozerye: [
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  ],
  okunevaya: [
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
  "sea-cruise": [
    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
  ],
  safari: [
    "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80",
  ],
  ocean: [
    "https://images.unsplash.com/photo-1497449493050-aad1e7cad165?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  ],
  livadia: [
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
  ],
  sestra: [
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
  ],
  putyatin: [
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
  lotus: [
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80",
  ],
  vladivostok1: [
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  ],
  botsad: [
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
  ],
  vladivostok2: [
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
  waterfall: [
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  ],
  individual: [
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
};

// ── MOCK-ФОЛЛБЭК ДЛЯ apiFetch ─────────────────────────────────────────────
function mockApiFallback(path, options = {}) {
  if (path === "/api/tours") return Promise.resolve(toursData);
  if (path === "/api/user/tours") return Promise.resolve(mockUserTours);
  if (path === "/api/user/achievements") return Promise.resolve(achievementsList);

  // [FIX-1] Mock auth УДАЛЁН — вход только через реальный бэкенд.
  // Если бэкенд недоступен — пользователь видит ошибку, а не фантомный вход.

  if (path === "/api/auth/me") return Promise.resolve(null);
  if (path === "/api/bookings") return Promise.resolve({ ok: true });
  return Promise.resolve(null);
}

// ── ТОСТ-УВЕДОМЛЕНИЕ ────────────────────────────────────────────────────────
function showToast(msg) {
  let toast = document.getElementById("toastMsg");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toastMsg";
    toast.className = "toast-msg";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

// ── НАВИГАЦИЯ / ПРОФИЛЬ / AUTH MODAL ────────────────────────────────────────
function toggleProfile() {
  const panel = document.getElementById("sideProfile");
  if (!panel) return;
  panel.classList.toggle("open");
}

function toggleAuthModal() {
  const modal = document.getElementById("authModal");
  if (!modal) return;
  modal.classList.toggle("open");
}

function openBookingGeneral() {
  const modal = document.getElementById("bookingModal");
  if (!modal) return;
  // Сброс выбора даты
  selectedDateStr = "";
  buildCalendar("miniCalendarPlaceholder", null);
  modal.classList.add("open");
}

// ── РЕНДЕР КАРТОЧЕК ТУРОВ ────────────────────────────────────────────────────
function renderTours(tours) {
  const container = document.getElementById("toursContainer");
  if (!container) return;
  container.innerHTML = "";

  tours.forEach((tour) => {
    const card = document.createElement("div");
    card.className = "tour-card";
    card.dataset.id = tour.id;

    const scheduleHtml = tour.schedule
      ? `<div style="font-size:0.7rem;color:rgba(255,255,255,0.5);margin-bottom:6px;letter-spacing:0.3px">${tour.schedule}${tour.departure ? " · " + tour.departure : ""}${tour.duration ? " · " + tour.duration : ""}</div>`
      : "";
    card.innerHTML = `
      <div class="tour-img-placeholder" style="background-image:url('${tour.img}')"></div>
      <div class="tour-static-title">
        <span class="tour-card-tag-inline">${tour.tag}</span>
        <p class="tour-name">${tour.name}</p>
      </div>
      <div class="tour-hover-info">
        <span class="tour-tag" style="color:var(--accent-liquid)">${tour.tag}</span>
        <h3 class="tour-name">${tour.name}</h3>
        ${scheduleHtml}
        <p class="tour-desc">${tour.desc}</p>
        <div class="tour-meta">
          <span class="tour-price">${tour.price} <span>₽/чел</span></span>
          <button class="tour-btn" data-action="openTourDetail" data-id="${tour.id}">
            Подробнее
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// ── МОДАЛЬНОЕ ОКНО ДЕТАЛИ ТУРА ───────────────────────────────────────────────
let detailSlideIndex = 0;
let detailSlides = [];
let detailCalYear = 2026;
let detailCalMonth = 5; // 0-based = июнь

function openTourDetail(tourId) {
  const tour = toursData.find((t) => t.id === tourId);
  if (!tour) return;

  const slides = tourSlides[tourId] || [tour.img];
  detailSlides = slides;
  detailSlideIndex = 0;
  detailCalYear = calYear;
  detailCalMonth = calMonth;

  // Удаляем старую модалку если есть
  const old = document.getElementById("tourDetailModal");
  if (old) old.remove();

  // Строим слайдер
  const dotsHtml = slides
    .map((_, i) => `<div class="slider-dot${i === 0 ? " active" : ""}" data-idx="${i}"></div>`)
    .join("");

  const slidesHtml = slides
    .map((url) => `<div class="tour-slide" style="background-image:url('${url}')"></div>`)
    .join("");

  // Строим выпадающий список дат (свободные даты = не в bookedDates)
  const freeDates = getFreeDatesForTour(tour);
  const dateOptions = freeDates.length
    ? freeDates.map((d) => `<option value="${d}">${formatDateRu(d)}</option>`).join("")
    : `<option value="">Нет доступных дат</option>`;

  const modal = document.createElement("div");
  modal.className = "modal-tour-detail";
  modal.id = "tourDetailModal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");

  modal.innerHTML = `
    <div class="tour-detail-container">
      <div class="tour-slider">
        <div class="tour-slider-track" id="detailSliderTrack">${slidesHtml}</div>
        <button class="slider-btn slider-btn--prev" id="sliderPrev" aria-label="Назад">&#8249;</button>
        <button class="slider-btn slider-btn--next" id="sliderNext" aria-label="Вперёд">&#8250;</button>
        <div class="slider-dots" id="sliderDots">${dotsHtml}</div>
      </div>
      <div class="tour-detail-body">
        <button class="tour-detail-close" id="closeTourDetail" aria-label="Закрыть">&times;</button>
        <div>
          <span class="tour-detail-tag">${tour.tag}</span>
          <h2 class="tour-detail-title">${tour.name}</h2>
        </div>
        <p class="tour-detail-desc">${tour.desc}</p>
        <div class="tour-detail-info-row">
          <div class="tour-detail-info-chip">💰 <span>Цена: <strong>${tour.price} ₽</strong>/чел</span></div>
          <div class="tour-detail-info-chip">📍 <span>Приморский Край</span></div>
          <div class="tour-detail-info-chip">👥 <span>Группы до <strong>12</strong> чел</span></div>
        </div>
        <div class="tour-detail-booking">
          <h4>Выбрать дату и забронировать</h4>
          <div class="tour-detail-booking-row">
            <div class="detail-form-group">
              <label for="detailDateSelect">Дата</label>
              <select id="detailDateSelect">${dateOptions}</select>
            </div>
            <div class="detail-form-group">
              <label for="detailTimeSelect">Время</label>
              <select id="detailTimeSelect">
                <option value="09:00">Утро (09:00)</option>
                <option value="14:00">День (14:00)</option>
                <option value="19:00">Вечер (19:00)</option>
              </select>
            </div>
          </div>
          <div class="tour-detail-calendar">
            <div id="detailCalendarPlaceholder"></div>
          </div>
          <button class="btn-book-detail" id="btnBookFromDetail" data-id="${tour.id}">
            Забронировать →
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Открываем с анимацией
  requestAnimationFrame(() => modal.classList.add("open"));

  // Строим календарь в модалке тура
  buildCalendar("detailCalendarPlaceholder", tour.bookedDates || []);

  // Слайдер: кнопки
  document.getElementById("sliderPrev").addEventListener("click", () => moveSlider(-1));
  document.getElementById("sliderNext").addEventListener("click", () => moveSlider(1));

  // Слайдер: точки
  document.getElementById("sliderDots").addEventListener("click", (e) => {
    const dot = e.target.closest(".slider-dot");
    if (dot) moveSliderTo(Number(dot.dataset.idx));
  });

  // Закрытие
  document.getElementById("closeTourDetail").addEventListener("click", closeTourDetail);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeTourDetail();
  });

  // Кнопка бронирования из модалки тура
  document.getElementById("btnBookFromDetail").addEventListener("click", () => {
    const dateVal = document.getElementById("detailDateSelect").value;
    const timeVal = document.getElementById("detailTimeSelect").value;
    closeTourDetail();
    // Открываем общую форму бронирования и предзаполняем
    openBookingGeneral();
    setTimeout(() => {
      const tourSelect = document.getElementById("bookTourSelect");
      if (tourSelect) {
        // Находим option по id тура
        for (const opt of tourSelect.options) {
          if (opt.value === tour.id) {
            opt.selected = true;
            break;
          }
        }
      }
      if (dateVal) selectedDateStr = dateVal;
      buildCalendar("miniCalendarPlaceholder", tour.bookedDates || []);
      const timeSelect = document.getElementById("bookTime");
      if (timeSelect && timeVal) timeSelect.value = timeVal;
    }, 100);
  });
}

function closeTourDetail() {
  const modal = document.getElementById("tourDetailModal");
  if (!modal) return;
  modal.classList.remove("open");
  setTimeout(() => modal.remove(), 380);
}

function moveSlider(dir) {
  moveSliderTo(detailSlideIndex + dir);
}

function moveSliderTo(idx) {
  const count = detailSlides.length;
  detailSlideIndex = ((idx % count) + count) % count;
  const track = document.getElementById("detailSliderTrack");
  if (track) track.style.transform = `translateX(-${detailSlideIndex * 100}%)`;
  document.querySelectorAll(".slider-dot").forEach((d, i) => {
    d.classList.toggle("active", i === detailSlideIndex);
  });
}

// ── ВСПОМОГАТЕЛЬНЫЕ ДЛЯ ДАТ ─────────────────────────────────────────────────
function getFreeDatesForTour(tour) {
  const booked = new Set(tour.bookedDates || []);
  const result = [];
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth() + 2, 0); // 2 месяца вперёд
  let d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  while (d <= end && result.length < 20) {
    const str = d.toISOString().slice(0, 10);
    if (!booked.has(str)) result.push(str);
    d.setDate(d.getDate() + 1);
  }
  return result;
}

function formatDateRu(str) {
  const d = new Date(str + "T00:00:00");
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

// ── МИНИ-КАЛЕНДАРЬ ───────────────────────────────────────────────────────────
const RU_MONTHS = [
  "Январь","Февраль","Март","Апрель","Май","Июнь",
  "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"
];

function buildCalendar(placeholderId, bookedDates) {
  const el = document.getElementById(placeholderId);
  if (!el) return;

  const bSet = new Set(bookedDates || []);
  const today = new Date();

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const offset = (firstDay + 6) % 7; // пн=0
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  let daysHtml = "";
  for (let i = 0; i < offset; i++) daysHtml += `<div class="cal-day empty-day"></div>`;
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const isPast = new Date(dateStr + "T00:00:00") < today;
    const isBooked = bSet.has(dateStr);
    const isSelected = dateStr === selectedDateStr;
    let cls = "cal-day ";
    if (isPast || isBooked) cls += "booked-out";
    else if (isSelected) cls += "selected";
    else cls += "available";
    daysHtml += `<div class="${cls}" data-date="${dateStr}">${d}</div>`;
  }

  el.innerHTML = `
    <div class="mini-calendar-container">
      <div class="calendar-header">
        <button class="calendar-nav-btn" data-cal-nav="-1" data-cal-target="${placeholderId}" data-cal-booked='${JSON.stringify([...bSet])}' aria-label="Пред. месяц">&#8249;</button>
        <span class="calendar-month-year">${RU_MONTHS[calMonth]} ${calYear}</span>
        <button class="calendar-nav-btn" data-cal-nav="1" data-cal-target="${placeholderId}" data-cal-booked='${JSON.stringify([...bSet])}' aria-label="След. месяц">&#8250;</button>
      </div>
      <div class="calendar-weekdays">
        <span>Пн</span><span>Вт</span><span>Ср</span><span>Чт</span><span>Пт</span><span>Сб</span><span>Вс</span>
      </div>
      <div class="calendar-days-grid">${daysHtml}</div>
    </div>
  `;

  // Выбор даты
  el.querySelectorAll(".cal-day.available").forEach((day) => {
    day.addEventListener("click", () => {
      selectedDateStr = day.dataset.date;
      buildCalendar(placeholderId, bookedDates);
    });
  });

  // Навигация по месяцам
  el.querySelectorAll(".calendar-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.dataset.calNav);
      const booked = JSON.parse(btn.dataset.calBooked || "[]");
      calMonth += dir;
      if (calMonth < 0) { calMonth = 11; calYear--; }
      if (calMonth > 11) { calMonth = 0; calYear++; }
      buildCalendar(placeholderId, booked);
    });
  });
}

// ── ПРОФИЛЬ: ВКЛАДКИ ─────────────────────────────────────────────────────────
function initProfileTabs() {
  const tabBtns = document.querySelectorAll(".p-tab-btn");
  const tabPanels = document.querySelectorAll(".profile-tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.tab);
      tabBtns.forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
      tabPanels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const panel = document.getElementById(`pTab${idx + 1}`);
      if (panel) panel.classList.add("active");
    });
  });
}

// ── ПРОФИЛЬ: ФИЛЬТРЫ ТУРОВ ───────────────────────────────────────────────────
let currentFilter = "all";

function initTourFilters() {
  const filterBtns = document.querySelectorAll(".filter-chip");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      if (typeof loadMyBookings === 'function') loadMyBookings(); else renderUserTours([]);
    });
  });
}

const STATUS_LABEL = {
  booked: { label: "Предстоящий", color: "#3fd0ca" },
  started: { label: "В процессе", color: "#f59e0b" },
  completed: { label: "Завершён", color: "#10b981" },
};

function renderUserTours(tours) {
  const list = document.getElementById("toursList");
  if (!list) return;

  const filtered = currentFilter === "all"
    ? tours
    : tours.filter((t) => t.status === currentFilter);

  // Счётчик
  const counts = {
    booked: tours.filter(t => t.status === "booked").length,
    started: tours.filter(t => t.status === "started").length,
    completed: tours.filter(t => t.status === "completed").length,
  };

  // Обновляем статистику в шапке профиля
  const statTours = document.getElementById("statTours");
  if (statTours) statTours.textContent = tours.length;
  const statCompleted = document.getElementById("statCompleted");
  if (statCompleted) statCompleted.textContent = counts.completed;
  const statsHtml = `
    <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">
      <div style="flex:1;min-width:70px;background:rgba(63,208,202,.07);border:1px solid rgba(63,208,202,.18);border-radius:10px;padding:10px 12px;text-align:center">
        <div style="font-size:1.3rem;font-weight:800;color:var(--accent-liquid)">${counts.booked}</div>
        <div style="font-size:.65rem;color:rgba(255,255,255,.5);margin-top:2px">Предстоящих</div>
      </div>
      <div style="flex:1;min-width:70px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:10px 12px;text-align:center">
        <div style="font-size:1.3rem;font-weight:800;color:#f59e0b">${counts.started}</div>
        <div style="font-size:.65rem;color:rgba(255,255,255,.5);margin-top:2px">В процессе</div>
      </div>
      <div style="flex:1;min-width:70px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:10px 12px;text-align:center">
        <div style="font-size:1.3rem;font-weight:800;color:#10b981">${counts.completed}</div>
        <div style="font-size:.65rem;color:rgba(255,255,255,.5);margin-top:2px">Завершено</div>
      </div>
    </div>
  `;

  if (!filtered.length) {
    list.innerHTML = statsHtml + `
      <div style="text-align:center;padding:28px 10px;color:rgba(255,255,255,0.4)">
        <div style="font-size:2rem;margin-bottom:8px">🥾</div>
        <p style="font-size:.85rem;line-height:1.5">Туров в этой категории пока нет.<br>
        <a href="#tours-anchor" style="color:var(--accent-liquid);font-weight:700;text-decoration:none" onclick="document.getElementById('sideProfile').classList.remove('open')">Выбрать маршрут →</a></p>
      </div>`;
    return;
  }

  const toursHtml = filtered.map((t) => {
    const s = STATUS_LABEL[t.status] || { label: t.status, color: "#aaa" };
    return `
      <div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.07);align-items:center">
        <img src="${t.img}" alt="${t.name}" style="width:56px;height:56px;object-fit:cover;border-radius:10px;flex-shrink:0">
        <div style="flex:1;min-width:0">
          <p style="font-weight:700;font-size:.88rem;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${t.name}</p>
          <p style="font-size:.72rem;color:rgba(255,255,255,.45);margin-bottom:5px">${formatDateRu(t.date)}</p>
          <span style="font-size:.68rem;font-weight:700;color:${s.color};background:${s.color}22;padding:2px 9px;border-radius:20px">${s.label}</span>
        </div>
        <span style="font-weight:800;font-size:.88rem;white-space:nowrap;color:#fff;flex-shrink:0">${t.price} ₽</span>
      </div>
    `;
  }).join("");

  list.innerHTML = statsHtml + toursHtml;
}

// ── ПРОФИЛЬ: ДОСТИЖЕНИЯ ──────────────────────────────────────────────────────
function renderAchievements(list) {
  const grid = document.getElementById("achGrid");
  if (!grid) return;
  grid.innerHTML = list.map((a) => {
    const title = a.titleRu || a.title || "";
    const desc  = a.descRu  || a.description || "";
    return `
    <div class="ach-item${a.unlocked ? "" : " locked"}" title="${desc}">
      <div class="ach-icon">${a.icon}</div>
      <p class="ach-title">${title}</p>
      ${a.unlocked ? `<div class="ach-check">✓</div>` : `<div class="ach-lock">🔒</div>`}
    </div>
  `;
  }).join("");

  // Прогресс + счётчик в шапке
  const unlocked = list.filter((a) => a.unlocked).length;
  const total = list.length;
  const label = document.getElementById("achProgressLabel");
  if (label) label.textContent = `Открыто ${unlocked} из ${total}`;
  const fill = document.getElementById("achProgressFill");
  if (fill) fill.style.width = total ? `${Math.round((unlocked / total) * 100)}%` : "0%";
  const statAch = document.getElementById("statAch");
  if (statAch) statAch.textContent = unlocked;
}

// ── ЗАПОЛНИТЬ ВЫПАДАЮЩИЙ СПИСОК ТУРОВ В ФОРМЕ БРОНИРОВАНИЯ ───────────────────
function populateTourSelect() {
  const sel = document.getElementById("bookTourSelect");
  if (!sel) return;
  sel.innerHTML = toursData
    .map((t) => `<option value="${t.id}">${t.name} — ${t.price} ₽</option>`)
    .join("");
}

// ── NICKNAME INLINE EDIT ─────────────────────────────────────────────────────
function initNicknameEdit() {
  const wrapper = document.getElementById("nicknameWrapper");
  const nameEl = document.getElementById("profileName");
  if (!wrapper || !nameEl) return;

  // Добавляем sub-текст (email/статус)
  if (!document.getElementById("profileSub")) {
    const sub = document.createElement("span");
    sub.id = "profileSub";
    sub.className = "profile-sub";
    sub.textContent = "Участник клуба";
    wrapper.appendChild(sub);
  }

  const startEdit = () => {
    if (wrapper.querySelector("input")) return;
    const input = document.createElement("input");
    input.className = "nickname-input";
    input.value = nameEl.textContent.trim();
    input.style.cssText = "background:rgba(255,255,255,.1);border:1px solid var(--accent-liquid);border-radius:6px;color:#fff;padding:4px 10px;font-size:1rem;width:160px;outline:none;max-width:100%";
    wrapper.replaceChild(input, nameEl);
    input.focus();
    input.select();

    const save = () => {
      const val = input.value.trim() || localStorage.getItem("username") || "Пользователь";
      nameEl.textContent = val;
      wrapper.replaceChild(nameEl, input);
      // [FIX-1] Сохраняем через API если авторизован
      if (isUserLoggedIn && typeof saveNicknameToAPI === "function") {
        saveNicknameToAPI(val);
      } else {
        localStorage.setItem("username", val);
      }
    };
    input.addEventListener("blur", save);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") save();
      if (e.key === "Escape") wrapper.replaceChild(nameEl, input);
    });
  };

  nameEl.addEventListener("click", startEdit);
  nameEl.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") startEdit(); });
}

// ── ПЕРЕВОДЫ ─────────────────────────────────────────────────────────────────
function applyTranslations(lang) {
  const t = (typeof translations !== "undefined" && translations[lang]) ? translations[lang] : null;
  if (!t) return;

  // Переводим по id
  Object.entries(t).forEach(([id, text]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === "sec1H2" || id === "heroP" || id === "sec1Txt") {
      el.innerHTML = text;
    } else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      el.placeholder = text;
    } else {
      el.textContent = text;
    }
  });

  // Кнопка языка
  const langBtn = document.getElementById("langBtn");
  if (langBtn) langBtn.textContent = lang;
}

// ── ОСНОВНАЯ ИНИЦИАЛИЗАЦИЯ ───────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {

  // Восстановить имя и аватар из localStorage (до ответа сервера — без мигания)
  const savedFull   = localStorage.getItem("full_name");
  const savedName   = localStorage.getItem("username");
  const savedAvatar = localStorage.getItem("avatar_url");
  if (savedName) {
    const nameEl = document.getElementById("profileName");
    if (nameEl) nameEl.textContent = savedFull || savedName;
    const subEl = document.getElementById("profileSub");
    if (subEl) subEl.textContent = savedName;
  }
  if (savedAvatar) {
    const avatarEl = document.getElementById("profileAvatar");
    if (avatarEl) avatarEl.src = savedAvatar;
  }

  // Рендер туров — только 7 самых популярных
  renderTours(toursData.slice(0, 7));
  // Данные профиля загружаются через loadProfileData() в app.js после проверки сессии
  populateTourSelect();

  // Профиль-вкладки и фильтры
  initProfileTabs();
  initTourFilters();
  initNicknameEdit();

  // Проверяем сессию (определена в app.js)
  if (typeof checkExistingSession === "function") checkExistingSession();

  // Google callback
  if (typeof handleGoogleCallback === "function") handleGoogleCallback();

  // ── ДЕЛЕГИРОВАНИЕ СОБЫТИЙ ────────────────────────────────────────────────

  // Кнопка профиля
  document.getElementById("profileTrigger")?.addEventListener("click", () => {
    if (isUserLoggedIn) {
      toggleProfile();
    } else {
      toggleAuthModal();
    }
  });

  // Мобильная кнопка профиля
  document.getElementById("mobileProfileTrigger")?.addEventListener("click", () => {
    if (isUserLoggedIn) {
      toggleProfile();
    } else {
      toggleAuthModal();
    }
  });

  // Закрытие профиля
  document.getElementById("closeProfileBtn")?.addEventListener("click", () => {
    document.getElementById("sideProfile").classList.remove("open");
  });

  // Закрытие auth modal
  document.getElementById("closeAuthBtn")?.addEventListener("click", toggleAuthModal);

  // Закрытие booking modal
  document.getElementById("closeBookingBtn")?.addEventListener("click", () => {
    document.getElementById("bookingModal").classList.remove("open");
  });

  // Закрытие по клику вне контейнера
  document.getElementById("authModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("authModal")) toggleAuthModal();
  });
  document.getElementById("bookingModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("bookingModal"))
      document.getElementById("bookingModal").classList.remove("open");
  });

  // Auth tabs (Вход / Регистрация)
  document.querySelectorAll(".auth-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab-btn").forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      currentAuthMode = btn.dataset.mode;
      const form = document.getElementById("authMainForm");
      if (form) {
        form.classList.toggle("auth-mode-register", currentAuthMode === "register");
      }
      const submitBtn = document.getElementById("authSubmitBtn");
      if (submitBtn) submitBtn.textContent = currentAuthMode === "login" ? "Войти" : "Зарегистрироваться";
    });
  });

  // Auth form submit
  document.getElementById("authMainForm")?.addEventListener("submit", (e) => {
    if (typeof handleAuthSubmit === "function") handleAuthSubmit(e);
  });

  // Logout
  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    if (typeof handleLogout === "function") handleLogout();
  });

  // VK / Google login
  document.querySelector(".social-btn--vk")?.addEventListener("click", () => {
    if (typeof loginWithVK === "function") loginWithVK();
  });
  document.getElementById("googleLoginBtn")?.addEventListener("click", () => {
    if (typeof loginWithGoogle === "function") loginWithGoogle();
  });

  // data-action="openBookingGeneral" (кнопки «Забронировать» и «В путь»)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const action = btn.dataset.action;

    if (action === "openBookingGeneral") {
      openBookingGeneral();
    }
    if (action === "openTourDetail") {
      openTourDetail(btn.dataset.id);
    }
  });

  // Клик на карточку тура (не на кнопку «Подробнее»)
  document.getElementById("toursContainer")?.addEventListener("click", (e) => {
    if (e.target.closest("[data-action='openTourDetail']")) return; // кнопка — свой обработчик
    const card = e.target.closest(".tour-card");
    if (card && card.dataset.id) {
      openTourDetail(card.dataset.id);
    }
  });

  // Кнопка «Все туры» / переключение вида
  document.getElementById("toggleGridBtn")?.addEventListener("click", () => {
    isGridViewActive = !isGridViewActive;
    const container = document.getElementById("toursContainer");
    const btnText = document.getElementById("txtBtnAll");
    container?.classList.toggle("view-all-cards", isGridViewActive);
    if (btnText) btnText.textContent = isGridViewActive ? "Свернуть" : "Все туры";
  });

  // Форма бронирования
  document.getElementById("bookingForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("bookSubmitBtn");
    if (btn) btn.disabled = true;

    const payload = {
      full_name: document.getElementById("bookName").value.trim(),
      phone: document.getElementById("bookPhone").value.trim(),
      email: document.getElementById("bookEmail").value.trim(),
      tour_id: document.getElementById("bookTourSelect").value,
      date: selectedDateStr,
      time: document.getElementById("bookTime").value,
      people_count: Number(document.getElementById("bookPeopleCount").value),
      message: document.getElementById("bookMessage").value.trim(),
    };

    if (!payload.full_name || !payload.phone || !payload.tour_id || !payload.date) {
      alert("Пожалуйста, заполните обязательные поля и выберите дату.");
      if (btn) btn.disabled = false;
      return;
    }

    try {
      await apiFetch("/api/bookings", { method: "POST", body: JSON.stringify(payload) });
      document.getElementById("bookingModal").classList.remove("open");
      showToast("Заявка отправлена! Мы свяжемся с вами.");
    } catch {
      showToast("Ошибка при отправке. Попробуйте ещё раз.");
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  // Реферал: копировать ссылку
  document.getElementById("btnCopy")?.addEventListener("click", () => {
    const inp = document.getElementById("refLink");
    if (!inp) return;
    navigator.clipboard.writeText(inp.value).then(() => showToast("Ссылка скопирована!"));
  });

  // Промокод: применить
  document.getElementById("btnApply")?.addEventListener("click", () => {
    const code = document.getElementById("promoInput")?.value.trim().toUpperCase();
    if (!code) return;
    // Заглушка — в продакшне запрос на /api/promo/apply
    const valid = ["PRIMORYE10", "LOTUS2026", "POHODNIK"];
    if (valid.includes(code)) {
      showToast(`Промокод ${code} применён! Скидка 10%`);
    } else {
      showToast("Промокод не найден или недействителен.");
    }
  });

  // Аватар
  document.getElementById("avatarTrigger")?.addEventListener("click", () => {
    document.getElementById("avatarFileInput")?.click();
  });
  document.getElementById("avatarFileInput")?.addEventListener("change", (e) => {
    if (typeof loadAvatarFromPC === "function") loadAvatarFromPC(e.target);
  });

  // Навигационные якоря
  document.querySelectorAll(".nav-target[href^='#']").forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") return;
      e.preventDefault();
      document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
    });
  });

  // Язык RU/EN
  document.getElementById("langBtn")?.addEventListener("click", () => {
    currentLang = currentLang === "RU" ? "EN" : "RU";
    applyTranslations(currentLang);
  });

  document.getElementById("heroBtn")?.addEventListener("click", (e) => {
    const toursAnchor = document.getElementById("tours-anchor");
    if (toursAnchor) {
      e.stopPropagation();
      toursAnchor.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  buildCalendar("miniCalendarPlaceholder", []);

  // Маркии отзывов: пауза при наведении
  const marquee = document.getElementById("marquee-line");
  if (marquee) {
    marquee.addEventListener("mouseenter", () => marquee.style.animationPlayState = "paused");
    marquee.addEventListener("mouseleave", () => marquee.style.animationPlayState = "running");
  }

});
