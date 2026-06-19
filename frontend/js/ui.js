// Escape user/API-supplied strings before inserting into innerHTML.
// Defined first so it's available to all rendering functions below.
// SECURITY: also escapes ' (not just "), so this stays safe even if a
// future call site interpolates into a single-quoted HTML attribute —
// every current call site happens to use double quotes, but that's an
// invariant this function shouldn't silently depend on.
function escHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

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
  "triozerye-classic": [
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  ],
  "okunevaya-jeep": [
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
  ],
  "boats-yachts": [
    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=900&q=80",
  ],
  "spokoinaya-jeep": [
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=80",
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

// * type: "default" | "success" | "error"
function showToast(msg, type = "default") {
  let toast = document.getElementById("toastMsg");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toastMsg";
    document.body.appendChild(toast);
  }
  toast.className = "toast-msg toast-" + type;
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toast._hideTimer);
  toast._hideTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

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

  selectedDateStr = "";
  buildCalendar("miniCalendarPlaceholder", null);
  modal.classList.add("open");
}

const WEEKDAYS = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
];

let selectedDay = null;

function isTourAvailableOnDay(tour, dayName) {
  const sched = tour && tour.schedule ? tour.schedule.trim() : "";
  if (sched === "Ежедневно") return true;
  if (WEEKDAYS.includes(sched)) return sched === dayName;
  return true;
}

function applyDayFilter() {
  const container = document.getElementById("toursContainer");
  if (!container) return 0;
  const cards = container.querySelectorAll(".tour-card");
  let availableCount = 0;
  cards.forEach((card) => {
    const tour = toursData.find((t) => t.id === card.dataset.id);
    if (!selectedDay) {
      card.classList.remove("tour-card--dimmed", "tour-card--match");
      return;
    }
    const ok = tour ? isTourAvailableOnDay(tour, selectedDay) : false;
    card.classList.toggle("tour-card--match", ok);
    card.classList.toggle("tour-card--dimmed", !ok);
    if (ok) availableCount++;
  });
  return availableCount;
}

function initDayFilter() {
  const panel = document.getElementById("dayFilter");
  if (!panel) return;
  const buttons = panel.querySelectorAll(".day-chip");

  const todayName = WEEKDAYS[(new Date().getDay() + 6) % 7];
  buttons.forEach((b) => {
    if (b.dataset.day === todayName) b.classList.add("is-today");
  });

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const day = btn.dataset.day;
      if (selectedDay === day) {
        selectedDay = null;
        buttons.forEach((b) => b.classList.remove("active"));
      } else {
        selectedDay = day;
        buttons.forEach((b) => b.classList.toggle("active", b === btn));
      }
      const count = applyDayFilter();
      if (selectedDay) {
        showToast(`${selectedDay}: доступно туров — ${count}`);
      }
    });
  });
}

function renderTours(tours) {
  const container = document.getElementById("toursContainer");
  if (!container) return;
  container.innerHTML = "";

  tours.forEach((tour) => {
    const card = document.createElement("div");
    card.className = "tour-card";
    card.dataset.id = tour.id;

    const scheduleHtml = tour.schedule
      ? `<div style="font-size:0.7rem;color:rgba(255,255,255,0.5);margin-bottom:6px;letter-spacing:0.3px">${escHtml(tour.schedule)}${tour.departure ? " · " + escHtml(tour.departure) : ""}${tour.duration ? " · " + escHtml(tour.duration) : ""}</div>`
      : "";
    card.innerHTML = `
      <div class="tour-img-placeholder" style="background-image:url('${encodeURI(tour.img || "")}')"></div>
      <div class="tour-static-title">
        <span class="tour-card-tag-inline">${escHtml(tour.tag)}</span>
        <p class="tour-name">${escHtml(tour.name)}</p>
      </div>
      <div class="tour-hover-info">
        <span class="tour-tag" style="color:var(--accent-liquid)">${escHtml(tour.tag)}</span>
        <h3 class="tour-name">${escHtml(tour.name)}</h3>
        ${scheduleHtml}
        <p class="tour-desc">${escHtml(tour.desc)}</p>
        <div class="tour-meta">
          <span class="tour-price">${escHtml(String(tour.price))} <span>₽/чел</span></span>
          <button class="tour-btn" data-action="openTourDetail" data-id="${escHtml(tour.id)}">
            Подробнее
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

let detailSlideIndex = 0;
let detailSlides = [];
let detailCalYear = 2026;
let detailCalMonth = 5;

function openTourDetail(tourId) {
  const tour = toursData.find((t) => t.id === tourId);
  if (!tour) return;

  const slides = tourSlides[tourId] || [tour.img];
  detailSlides = slides;
  detailSlideIndex = 0;
  detailCalYear = calYear;
  detailCalMonth = calMonth;

  const old = document.getElementById("tourDetailModal");
  if (old) old.remove();

  const dotsHtml = slides
    .map(
      (_, i) =>
        `<div class="slider-dot${i === 0 ? " active" : ""}" data-idx="${i}"></div>`,
    )
    .join("");

  const slidesHtml = slides
    .map(
      (url) =>
        `<div class="tour-slide" style="background-image:url('${url}')"></div>`,
    )
    .join("");

  const freeDates = getFreeDatesForTour(tour);
  const dateOptions = freeDates.length
    ? freeDates
        .map((d) => `<option value="${d}">${formatDateRu(d)}</option>`)
        .join("")
    : `<option value="">Нет доступных дат</option>`;
  selectedDateStr = freeDates.length ? freeDates[0] : "";

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
          <span class="tour-detail-tag">${escHtml(tour.tag)}</span>
          <h2 class="tour-detail-title">${escHtml(tour.name)}</h2>
        </div>
        <p class="tour-detail-desc">${escHtml(tour.desc)}</p>
        <div class="tour-detail-info-row">
          <div class="tour-detail-info-chip">💰 <span>Цена: <strong>${escHtml(String(tour.price))} ₽</strong>/чел</span></div>
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
          <button class="btn-book-detail" id="btnBookFromDetail" data-id="${escHtml(tour.id)}">
            Забронировать →
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  requestAnimationFrame(() => modal.classList.add("open"));

  const detailDateSelect = document.getElementById("detailDateSelect");

  buildCalendar(
    "detailCalendarPlaceholder",
    tour.bookedDates || [],
    (picked) => {
      if (
        detailDateSelect &&
        [...detailDateSelect.options].some((o) => o.value === picked)
      ) {
        detailDateSelect.value = picked;
      }
    },
  );

  if (detailDateSelect) {
    detailDateSelect.addEventListener("change", () => {
      selectedDateStr = detailDateSelect.value;
      buildCalendar(
        "detailCalendarPlaceholder",
        tour.bookedDates || [],
        (picked) => {
          if ([...detailDateSelect.options].some((o) => o.value === picked)) {
            detailDateSelect.value = picked;
          }
        },
      );
    });
  }

  document
    .getElementById("sliderPrev")
    .addEventListener("click", () => moveSlider(-1));
  document
    .getElementById("sliderNext")
    .addEventListener("click", () => moveSlider(1));

  document.getElementById("sliderDots").addEventListener("click", (e) => {
    const dot = e.target.closest(".slider-dot");
    if (dot) moveSliderTo(Number(dot.dataset.idx));
  });

  document
    .getElementById("closeTourDetail")
    .addEventListener("click", closeTourDetail);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeTourDetail();
  });

  document.getElementById("btnBookFromDetail").addEventListener("click", () => {
    const selectVal = document.getElementById("detailDateSelect").value;
    const dateVal = selectedDateStr || selectVal;
    const timeVal = document.getElementById("detailTimeSelect").value;
    closeTourDetail();

    openBookingGeneral();
    setTimeout(() => {
      const tourSelect = document.getElementById("bookTourSelect");
      if (tourSelect) {
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

function toLocalDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function getFreeDatesForTour(tour) {
  const booked = new Set(tour.bookedDates || []);
  const result = [];
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth() + 2, 0);
  let d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  while (d <= end && result.length < 20) {
    const str = toLocalDateStr(d);
    if (!booked.has(str)) result.push(str);
    d.setDate(d.getDate() + 1);
  }
  return result;
}

function formatDateRu(str) {
  const d = new Date(str + "T00:00:00");
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

const RU_MONTHS = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
];

function buildCalendar(placeholderId, bookedDates, onSelect) {
  const el = document.getElementById(placeholderId);
  if (!el) return;

  const bSet = new Set(bookedDates || []);
  const today = new Date();

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const offset = (firstDay + 6) % 7;
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  let daysHtml = "";
  for (let i = 0; i < offset; i++)
    daysHtml += `<div class="cal-day empty-day"></div>`;
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const isPast = new Date(dateStr + "T00:00:00") < today;
    const isBooked = bSet.has(dateStr);
    const isSelected = dateStr === selectedDateStr;
    let cls = "cal-day ";
    if (isBooked) cls += "booked-out";
    else if (isSelected) cls += "selected";
    else if (isPast) cls += "past-day";
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

  el.querySelectorAll(".cal-day.available, .cal-day.past-day").forEach(
    (day) => {
      day.addEventListener("click", () => {
        selectedDateStr = day.dataset.date;
        buildCalendar(placeholderId, bookedDates, onSelect);
        if (typeof onSelect === "function") onSelect(selectedDateStr);
      });
    },
  );

  el.querySelectorAll(".calendar-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.dataset.calNav);
      const booked = JSON.parse(btn.dataset.calBooked || "[]");
      calMonth += dir;
      if (calMonth < 0) {
        calMonth = 11;
        calYear--;
      }
      if (calMonth > 11) {
        calMonth = 0;
        calYear++;
      }
      buildCalendar(placeholderId, booked, onSelect);
    });
  });
}

function initProfileTabs() {
  const tabBtns = document.querySelectorAll(".p-tab-btn");
  const tabPanels = document.querySelectorAll(".profile-tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.tab);
      tabBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      tabPanels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const panel = document.getElementById(`pTab${idx + 1}`);
      if (panel) panel.classList.add("active");
    });
  });
}

let currentFilter = "all";

function initTourFilters() {
  const filterBtns = document.querySelectorAll(".filter-chip");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      if (typeof loadMyBookings === "function") loadMyBookings();
      else renderUserTours([]);
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

  const filtered =
    currentFilter === "all"
      ? tours
      : tours.filter((t) => t.status === currentFilter);

  const counts = {
    booked: tours.filter((t) => t.status === "booked").length,
    started: tours.filter((t) => t.status === "started").length,
    completed: tours.filter((t) => t.status === "completed").length,
  };

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
    list.innerHTML =
      statsHtml +
      `
      <div style="text-align:center;padding:28px 10px;color:rgba(255,255,255,0.4)">
        <div style="font-size:2rem;margin-bottom:8px">🥾</div>
        <p style="font-size:.85rem;line-height:1.5">Туров в этой категории пока нет.<br>
        <a href="#tours-anchor" style="color:var(--accent-liquid);font-weight:700;text-decoration:none" onclick="document.getElementById('sideProfile').classList.remove('open')">Выбрать маршрут →</a></p>
      </div>`;
    return;
  }

  const toursHtml = filtered
    .map((t) => {
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
    })
    .join("");

  list.innerHTML = statsHtml + toursHtml;
}

function renderAchievements(list) {
  const grid = document.getElementById("achGrid");
  if (!grid) return;
  grid.innerHTML = list
    .map((a) => {
      const title = a.titleRu || a.title || "";
      const desc = a.descRu || a.description || "";
      return `
    <div class="ach-item${a.unlocked ? "" : " locked"}" title="${desc}">
      <div class="ach-icon">${a.icon}</div>
      <p class="ach-title">${title}</p>
      ${a.unlocked ? `<div class="ach-check">✓</div>` : `<div class="ach-lock">🔒</div>`}
    </div>
  `;
    })
    .join("");

  const unlocked = list.filter((a) => a.unlocked).length;
  const total = list.length;
  const label = document.getElementById("achProgressLabel");
  if (label) label.textContent = `Открыто ${unlocked} из ${total}`;
  const fill = document.getElementById("achProgressFill");
  if (fill)
    fill.style.width = total
      ? `${Math.round((unlocked / total) * 100)}%`
      : "0%";
  const statAch = document.getElementById("statAch");
  if (statAch) statAch.textContent = unlocked;
}

function populateTourSelect() {
  const sel = document.getElementById("bookTourSelect");
  if (!sel) return;
  sel.innerHTML = toursData
    .map((t) => `<option value="${t.id}">${t.name} — ${t.price} ₽</option>`)
    .join("");
}

function initNicknameEdit() {
  const wrapper = document.getElementById("nicknameWrapper");
  const nameEl = document.getElementById("profileName");
  if (!wrapper || !nameEl) return;

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
    input.style.cssText =
      "background:rgba(255,255,255,.1);border:1px solid var(--accent-liquid);border-radius:6px;color:#fff;padding:4px 10px;font-size:1rem;width:160px;outline:none;max-width:100%";
    wrapper.replaceChild(input, nameEl);
    input.focus();
    input.select();

    const save = () => {
      const val =
        input.value.trim() ||
        localStorage.getItem("username") ||
        "Пользователь";
      nameEl.textContent = val;
      wrapper.replaceChild(nameEl, input);

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
  nameEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") startEdit();
  });
}

function applyTranslations(lang) {
  const t =
    typeof translations !== "undefined" && translations[lang]
      ? translations[lang]
      : null;
  if (!t) return;

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

  const langBtn = document.getElementById("langBtn");
  if (langBtn) langBtn.textContent = lang;
}

// ── REVIEWS ──
// Reviews now come from the API (GET /api/reviews) instead of being
// hardcoded in this file's markup, so this escaping helper matters here
// in a way it didn't for the old static copy: author_name/text can be
// real visitor input. Same rule as the admin panel — never interpolate
// it into innerHTML unescaped.

const REVIEW_AVATAR_COLORS = [
  "#1a4f5c", "#3b2f5c", "#2a4a2a", "#4a3a1a",
  "#22525c", "#194a5c", "#5c2a3a", "#3a4a5c",
];

function reviewAvatarColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return REVIEW_AVATAR_COLORS[hash % REVIEW_AVATAR_COLORS.length];
}

function reviewInitials(name) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return (parts[0][0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

function buildReviewCardHtml(r, hidden) {
  const tourLabel = r.tour_name ? escHtml(r.tour_name) : "Лотос Тур";
  const sourceTag = r.source === "2gis" ? " · 2ГИС" : "";
  return `
    <article class="review-card-item"${hidden ? ' aria-hidden="true"' : ""}>
      <div class="review-stars" aria-label="${r.rating} звёзд">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</div>
      <p class="review-text">«${escHtml(r.text)}»</p>
      <div class="review-author">
        <div class="review-avatar" style="background:${reviewAvatarColor(r.author_name)}">${escHtml(reviewInitials(r.author_name))}</div>
        <div>
          <span class="review-name">${escHtml(r.author_name)}</span>
          <span class="review-tour">${tourLabel}${sourceTag}</span>
        </div>
      </div>
    </article>`;
}

async function loadAndRenderReviews() {
  const line = document.getElementById("marquee-line");
  if (!line) return;
  const wrap = document.getElementById("marqueeWrapper");
  const summaryEl = document.getElementById("reviewsSummary");
  try {
    const data = await apiFetch("/api/reviews?limit=30");
    const list = data.reviews || [];

    if (summaryEl) {
      summaryEl.innerHTML = data.stats && data.stats.total_count
        ? `<span class="reviews-summary-stars">★ ${data.stats.average_rating.toFixed(1)}</span> на основе ${data.stats.total_count} отзывов`
        : "";
    }

    if (!list.length) {
      if (wrap) wrap.style.display = "none";
      return;
    }
    // The CSS marquee animation translates by exactly -50% of the track
    // width, assuming the content is duplicated — rendering the list
    // twice (second copy aria-hidden) is what makes the scroll loop
    // seamlessly regardless of how many real reviews exist.
    line.innerHTML =
      list.map((r) => buildReviewCardHtml(r, false)).join("") +
      list.map((r) => buildReviewCardHtml(r, true)).join("");
  } catch (e) {
    console.error("Не удалось загрузить отзывы:", e);
  }
}

let reviewFormRating = 0;

function setReviewFormRating(value) {
  reviewFormRating = value;
  document.querySelectorAll("#reviewStarPicker .star-picker-star").forEach((el) => {
    el.classList.toggle("is-active", Number(el.dataset.value) <= value);
  });
}

function populateReviewTourSelect() {
  const sel = document.getElementById("reviewTourSelect");
  if (!sel || typeof toursData === "undefined") return;
  sel.innerHTML =
    '<option value="">Без привязки к туру</option>' +
    toursData.map((t) => `<option value="${t.id}">${escHtml(t.name)}</option>`).join("");
}

function openReviewForm() {
  const modal = document.getElementById("reviewFormModal");
  if (!modal) return;
  const statusEl = document.getElementById("reviewFormStatus");
  statusEl.textContent = "";
  statusEl.className = "review-form-status";
  document.getElementById("reviewAuthorName").value = "";
  document.getElementById("reviewText").value = "";
  document.getElementById("reviewSubmitForm").style.display = "";
  setReviewFormRating(0);
  populateReviewTourSelect();
  modal.classList.add("open");
}
function closeReviewForm() {
  document.getElementById("reviewFormModal")?.classList.remove("open");
}

async function submitReviewForm(e) {
  e.preventDefault();
  const statusEl = document.getElementById("reviewFormStatus");
  const name = document.getElementById("reviewAuthorName").value.trim();
  const text = document.getElementById("reviewText").value.trim();
  const tourId = document.getElementById("reviewTourSelect").value || null;

  if (!name || !text || !reviewFormRating) {
    statusEl.textContent = "Заполните имя, оценку и текст отзыва.";
    statusEl.className = "review-form-status is-error";
    return;
  }

  const btn = document.getElementById("reviewSubmitBtn");
  btn.disabled = true;
  try {
    await apiFetch("/api/reviews", {
      method: "POST",
      body: JSON.stringify({
        author_name: name,
        rating: reviewFormRating,
        text,
        tour_id: tourId,
      }),
    });
    document.getElementById("reviewSubmitForm").style.display = "none";
    statusEl.textContent =
      "Спасибо! Отзыв отправлен на проверку и появится на сайте после одобрения модератором.";
    statusEl.className = "review-form-status is-success";
  } catch (err) {
    statusEl.textContent = err.message || "Не удалось отправить отзыв. Попробуйте позже.";
    statusEl.className = "review-form-status is-error";
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const savedFull = localStorage.getItem("full_name");
  const savedName = localStorage.getItem("username");
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

  renderTours(toursData.slice(0, 7));

  populateTourSelect();
  loadAndRenderReviews();

  initProfileTabs();
  initTourFilters();
  initNicknameEdit();
  initDayFilter();
  applyDayFilter();

  if (typeof checkExistingSession === "function") checkExistingSession();

  if (typeof handleGoogleCallback === "function") handleGoogleCallback();

  document.getElementById("profileTrigger")?.addEventListener("click", () => {
    if (isUserLoggedIn) {
      toggleProfile();
    } else {
      toggleAuthModal();
    }
  });

  document
    .getElementById("mobileProfileTrigger")
    ?.addEventListener("click", () => {
      if (isUserLoggedIn) {
        toggleProfile();
      } else {
        toggleAuthModal();
      }
    });

  document.getElementById("closeProfileBtn")?.addEventListener("click", () => {
    document.getElementById("sideProfile").classList.remove("open");
  });

  document
    .getElementById("closeAuthBtn")
    ?.addEventListener("click", toggleAuthModal);

  document.getElementById("closeBookingBtn")?.addEventListener("click", () => {
    document.getElementById("bookingModal").classList.remove("open");
  });

  document.getElementById("authModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("authModal")) toggleAuthModal();
  });
  document.getElementById("bookingModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("bookingModal"))
      document.getElementById("bookingModal").classList.remove("open");
  });

  document.getElementById("closeReviewFormBtn")?.addEventListener("click", closeReviewForm);
  document.getElementById("reviewFormModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("reviewFormModal")) closeReviewForm();
  });
  document.getElementById("openReviewFormBtn")?.addEventListener("click", openReviewForm);
  document.getElementById("reviewSubmitForm")?.addEventListener("submit", submitReviewForm);
  document.querySelectorAll("#reviewStarPicker .star-picker-star").forEach((el) => {
    el.addEventListener("click", () => setReviewFormRating(Number(el.dataset.value)));
  });

  document.getElementById("openCooperationBtn")?.addEventListener("click", () => {
    document.getElementById("cooperationModal").classList.add("open");
  });
  document.getElementById("closeCooperationBtn")?.addEventListener("click", () => {
    document.getElementById("cooperationModal").classList.remove("open");
  });
  document.getElementById("cooperationModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("cooperationModal"))
      document.getElementById("cooperationModal").classList.remove("open");
  });

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
        form.classList.toggle(
          "auth-mode-register",
          currentAuthMode === "register",
        );
      }
      const submitBtn = document.getElementById("authSubmitBtn");
      if (submitBtn)
        submitBtn.textContent =
          currentAuthMode === "login" ? "Войти" : "Зарегистрироваться";
    });
  });

  document.getElementById("authMainForm")?.addEventListener("submit", (e) => {
    if (typeof handleAuthSubmit === "function") handleAuthSubmit(e);
  });

  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    if (typeof handleLogout === "function") handleLogout();
  });

  document.querySelector(".social-btn--vk")?.addEventListener("click", () => {
    if (typeof loginWithVK === "function") loginWithVK();
  });
  document.getElementById("googleLoginBtn")?.addEventListener("click", () => {
    if (typeof loginWithGoogle === "function") loginWithGoogle();
  });

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

  document.getElementById("toursContainer")?.addEventListener("click", (e) => {
    if (e.target.closest("[data-action='openTourDetail']")) return;
    const card = e.target.closest(".tour-card");
    if (card && card.dataset.id) {
      openTourDetail(card.dataset.id);
    }
  });

  document.getElementById("toggleGridBtn")?.addEventListener("click", () => {
    isGridViewActive = !isGridViewActive;
    const container = document.getElementById("toursContainer");
    const btnText = document.getElementById("txtBtnAll");
    renderTours(isGridViewActive ? toursData : toursData.slice(0, 7));
    container?.classList.toggle("view-all-cards", isGridViewActive);
    if (btnText)
      btnText.textContent = isGridViewActive ? "Свернуть" : "Все туры";
    applyDayFilter();
  });

  document
    .getElementById("bookingForm")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("bookSubmitBtn");
      if (btn) btn.disabled = true;

      const contactEl = document.querySelector(
        'input[name="bookContact"]:checked',
      );
      const tgUsername =
        document.getElementById("bookTgUsername")?.value.trim() || "";

      // Validate Telegram username if selected
      if (contactEl && contactEl.value === "telegram" && !tgUsername) {
        const tgInput = document.getElementById("bookTgUsername");
        const tgErr = document.getElementById("tgFieldError");
        if (tgInput) {
          tgInput.classList.add("input-error");
          tgInput.focus();
        }
        if (tgErr) tgErr.style.display = "flex";
        if (btn) btn.disabled = false;
        return;
      }
      // Validate phone for Max contact
      if (contactEl && contactEl.value === "phone") {
        const phoneEl = document.getElementById("bookPhone");
        if (phoneEl && !phoneEl.value.trim()) {
          phoneEl.style.borderColor = "#ef4444";
          phoneEl.focus();
          showToast("Введите номер телефона для связи через Макса.", "error");
          if (btn) btn.disabled = false;
          return;
        }
      }

      const payload = {
        first_name: document.getElementById("bookName").value.trim(),
        phone: document.getElementById("bookPhone").value.trim(),
        email: document.getElementById("bookEmail").value.trim(),
        tour_id: document.getElementById("bookTourSelect").value,
        tour_date: selectedDateStr,
        preferred_time: document.getElementById("bookTime").value,
        people_count: Number(document.getElementById("bookPeopleCount").value),
        contact_method: contactEl ? contactEl.value : "",
        tg_username: tgUsername || null,
        comment: document.getElementById("bookMessage").value.trim() || null,
      };

      if (
        !payload.first_name ||
        !payload.phone ||
        !payload.email ||
        !payload.tour_id ||
        !payload.tour_date
      ) {
        showToast("Пожалуйста, заполните обязательные поля и выберите дату.");
        if (btn) btn.disabled = false;
        return;
      }

      if (!payload.contact_method) {
        showToast("Выберите способ связи.");
        if (btn) btn.disabled = false;
        return;
      }

      try {
        await apiFetch("/api/bookings", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        document.getElementById("bookingModal").classList.remove("open");
        showToast("Заявка отправлена! Мы свяжемся с вами.");
        if (typeof loadMyBookings === "function" && isUserLoggedIn)
          loadMyBookings();
      } catch (err) {
        showToast(err.message || "Ошибка при отправке. Попробуйте ещё раз.");
      } finally {
        if (btn) btn.disabled = false;
      }
    });

  /* ── People counter ── */
  const pctrCounts = { cntAdults: 1, cntTeens: 0, cntKids: 0, cntSeniors: 0 };
  document.querySelectorAll(".pctr-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const isPlus = btn.dataset.dir === "1";
      const min = Number(btn.dataset.min ?? 0);
      if (isPlus) {
        pctrCounts[targetId]++;
      } else {
        if (pctrCounts[targetId] > min) pctrCounts[targetId]--;
      }
      const el = document.getElementById(targetId);
      if (el) el.textContent = pctrCounts[targetId];
      const total =
        pctrCounts.cntAdults +
        pctrCounts.cntTeens +
        pctrCounts.cntKids +
        pctrCounts.cntSeniors;
      const hidden = document.getElementById("bookPeopleCount");
      if (hidden) hidden.value = total;
    });
  });

  /* ── Contact sub-panels ── */
  function showContactPanel(value) {
    ["subWhatsapp", "subTelegram", "subMax"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = "none";
    });
    if (value === "whatsapp") {
      const el = document.getElementById("subWhatsapp");
      if (el) el.style.display = "block";
    } else if (value === "telegram") {
      const el = document.getElementById("subTelegram");
      if (el) el.style.display = "block";
    } else if (value === "phone") {
      const el = document.getElementById("subMax");
      // validate phone already in form — if empty, highlight
      const phoneEl = document.getElementById("bookPhone");
      if (el) el.style.display = "block";
      if (phoneEl && !phoneEl.value.trim()) {
        phoneEl.style.borderColor = "#ef4444";
        phoneEl.setAttribute(
          "title",
          "Введите номер телефона для звонка от Макса",
        );
      }
    }
  }

  document.querySelectorAll('input[name="bookContact"]').forEach((radio) => {
    radio.addEventListener("change", () => showContactPanel(radio.value));
  });

  /* ── Telegram help toggle ── */
  document.getElementById("tgHelpToggle")?.addEventListener("click", () => {
    const box = document.getElementById("tgHelpBox");
    if (!box) return;
    const isOpen = box.style.display === "block";
    box.style.display = isOpen ? "none" : "block";
    document.getElementById("tgHelpToggle").textContent = isOpen
      ? "Как найти свой юзернейм? →"
      : "Скрыть подсказку ↑";
  });

  document.getElementById("bookTgUsername")?.addEventListener("input", () => {
    document.getElementById("bookTgUsername").classList.remove("input-error");
    const tgErr = document.getElementById("tgFieldError");
    if (tgErr) tgErr.style.display = "none";
  });

  /* ── bookPhone border reset on input ── */
  document.getElementById("bookPhone")?.addEventListener("input", (e) => {
    e.target.style.borderColor = "";
    e.target.removeAttribute("title");
  });

  document.getElementById("btnCopy")?.addEventListener("click", () => {
    const inp = document.getElementById("refLink");
    if (!inp) return;
    navigator.clipboard
      .writeText(inp.value)
      .then(() => showToast("Ссылка скопирована!"));
  });

  document.getElementById("btnApply")?.addEventListener("click", async () => {
    const input = document.getElementById("promoInput");
    const code = input?.value.trim().toUpperCase();
    if (!code) return;
    if (!isUserLoggedIn) {
      showToast("Войдите в аккаунт, чтобы применить промокод.");
      return;
    }
    try {
      const data = await apiFetch("/api/promo/apply", {
        method: "POST",
        body: JSON.stringify({ code }),
      });
      showToast(data.message);
      if (input) input.value = "";
    } catch (err) {
      showToast(err.message || "Промокод не найден или недействителен.");
    }
  });

  document.getElementById("avatarTrigger")?.addEventListener("click", () => {
    document.getElementById("avatarFileInput")?.click();
  });
  document
    .getElementById("avatarFileInput")
    ?.addEventListener("change", (e) => {
      if (typeof loadAvatarFromPC === "function") loadAvatarFromPC(e.target);
    });

  document.querySelectorAll(".nav-target[href^='#']").forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") return;
      e.preventDefault();
      document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
    });
  });

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

  const marquee = document.getElementById("marquee-line");
  if (marquee) {
    marquee.addEventListener(
      "mouseenter",
      () => (marquee.style.animationPlayState = "paused"),
    );
    marquee.addEventListener(
      "mouseleave",
      () => (marquee.style.animationPlayState = "running"),
    );
  }
});
