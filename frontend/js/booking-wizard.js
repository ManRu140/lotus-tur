/* ============================================================
   booking-wizard.js
   Additive enhancements for index.html — does not modify any
   existing function in app.js / ui.js, only wires new UI on top
   of the DOM hooks they already expose.

   Responsibilities:
   1) Mobile burger menu (open/close, translation mirroring)
   2) Booking modal step wizard (Маршрут → Поездка → Контакты)
   3) Scroll-reveal animation for [data-reveal] elements
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

  /* ──────────────────────────────────────────────────────────
     1) MOBILE BURGER MENU
     ────────────────────────────────────────────────────────── */
  (function setupMobileNav() {
    const burger = document.getElementById("burgerBtn");
    const menu = document.getElementById("mobileNavMenu");
    if (!burger || !menu) return;

    function closeMenu() {
      burger.classList.remove("is-open");
      menu.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
      menu.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }
    function openMenu() {
      burger.classList.add("is-open");
      menu.classList.add("is-open");
      burger.setAttribute("aria-expanded", "true");
      menu.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }

    burger.addEventListener("click", () => {
      if (menu.classList.contains("is-open")) closeMenu();
      else openMenu();
    });

    // Close after tapping any link/button inside (let the existing
    // delegated nav-target / data-action handlers in ui.js run first).
    menu.querySelectorAll("a, button").forEach((el) => {
      el.addEventListener("click", () => closeMenu());
    });

    // Close on backdrop tap (clicking the empty overlay area itself).
    menu.addEventListener("click", (e) => {
      if (e.target === menu) closeMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("is-open")) closeMenu();
    });

    // The mobile lang button reuses the desktop button's existing
    // click handler instead of duplicating language-switch logic.
    document.getElementById("mobileLangBtn")?.addEventListener("click", () => {
      document.getElementById("langBtn")?.click();
    });

    // Mirror nav-link text (and the lang button label) from the
    // desktop versions, since translations.js targets ids m1-m4 /
    // langBtn only and an id cannot be duplicated on two elements.
    function syncMobileNavText() {
      ["1", "2", "3", "4"].forEach((n) => {
        const src = document.getElementById("m" + n);
        const dest = document.getElementById("mm" + n);
        if (src && dest) dest.textContent = src.textContent;
      });
      const langSrc = document.getElementById("langBtn");
      const langDest = document.getElementById("mobileLangBtn");
      if (langSrc && langDest) langDest.textContent = langSrc.textContent;
    }
    syncMobileNavText();

    // Keep mirroring in sync whenever the language is toggled, by
    // wrapping applyTranslations without touching its source.
    if (typeof window.applyTranslations === "function") {
      const originalApplyTranslations = window.applyTranslations;
      window.applyTranslations = function (lang) {
        originalApplyTranslations(lang);
        syncMobileNavText();
      };
    }
  })();

  /* ──────────────────────────────────────────────────────────
     2) BOOKING WIZARD (3 steps inside the existing #bookingForm)
     ────────────────────────────────────────────────────────── */
  (function setupBookingWizard() {
    const modal = document.getElementById("bookingModal");
    const steps = Array.from(document.querySelectorAll(".booking-step"));
    const progressSteps = Array.from(document.querySelectorAll(".booking-progress-step"));
    const progressLines = Array.from(document.querySelectorAll(".booking-progress-line"));
    const backBtn = document.getElementById("bookBackBtn");
    const nextBtn = document.getElementById("bookNextBtn");
    const submitBtn = document.getElementById("bookSubmitBtn");
    if (!modal || !steps.length || !backBtn || !nextBtn || !submitBtn) return;

    let current = 0;

    function render(direction) {
      steps.forEach((panel, i) => {
        const isActive = i === current;
        panel.classList.toggle("is-active", isActive);
        panel.classList.toggle("dir-back", isActive && direction === "back");
      });
      progressSteps.forEach((dot, i) => {
        dot.classList.toggle("is-active", i === current);
        dot.classList.toggle("is-done", i < current);
      });
      progressLines.forEach((line, i) => {
        line.classList.toggle("is-filled", i < current);
      });
      backBtn.hidden = current === 0;
      nextBtn.hidden = current === steps.length - 1;
      submitBtn.hidden = current !== steps.length - 1;
    }

    function goToStep(index, direction) {
      current = Math.max(0, Math.min(steps.length - 1, index));
      render(direction);
    }

    function focusFirstInvalid(el) {
      el.style.borderColor = "#ef4444";
      el.focus({ preventScroll: false });
      setTimeout(() => { el.style.borderColor = ""; }, 2000);
    }

    // Validates only the fields visible in the *current* step before
    // letting the user move on — mirrors the toast pattern already
    // used by the real submit handler in ui.js.
    function validateCurrentStep() {
      const stepEl = steps[current];
      const stepNum = stepEl.dataset.step;

      if (stepNum === "1") {
        const tourSelect = document.getElementById("bookTourSelect");
        const timeSelect = document.getElementById("bookTime");
        if (tourSelect && !tourSelect.value) {
          if (typeof showToast === "function") showToast("Выберите направление.");
          return false;
        }
        if (timeSelect && !timeSelect.value) {
          if (typeof showToast === "function") showToast("Выберите удобное время.");
          return false;
        }
        if (!selectedDateStr) {
          if (typeof showToast === "function") showToast("Выберите дату поездки в календаре.");
          return false;
        }
        return true;
      }

      if (stepNum === "2") {
        const nameEl = document.getElementById("bookName");
        if (nameEl && !nameEl.value.trim()) {
          if (typeof showToast === "function") showToast("Укажите ФИО.");
          focusFirstInvalid(nameEl);
          return false;
        }
        const peopleCount = Number(document.getElementById("bookPeopleCount")?.value || 0);
        if (!peopleCount || peopleCount < 1) {
          if (typeof showToast === "function") showToast("Укажите хотя бы одного путешественника.");
          return false;
        }
        return true;
      }

      return true;
    }

    nextBtn.addEventListener("click", () => {
      if (!validateCurrentStep()) return;
      goToStep(current + 1, "fwd");
    });

    backBtn.addEventListener("click", () => {
      goToStep(current - 1, "back");
    });

    // Reset the wizard to step 1 every time the booking modal opens,
    // regardless of entry point (nav link, tour card, schedule card,
    // tour-detail "Забронировать"), by wrapping openBookingGeneral
    // once — function declarations attach to window, so this is safe.
    if (typeof window.openBookingGeneral === "function") {
      const originalOpenBookingGeneral = window.openBookingGeneral;
      window.openBookingGeneral = function () {
        originalOpenBookingGeneral();
        goToStep(0);
      };
    }

    render();
  })();

  /* ──────────────────────────────────────────────────────────
     3) SCROLL-REVEAL for [data-reveal] elements
     ────────────────────────────────────────────────────────── */
  (function setupScrollReveal() {
    const targets = document.querySelectorAll("[data-reveal]");
    if (!targets.length) return;

    if (!("IntersectionObserver" in window)) {
      targets.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    targets.forEach((el) => observer.observe(el));
  })();

});
