const API = '/api';

async function loadPopularTours() {
  const container = document.getElementById('popular-tours-grid');
  if (!container) return;

  container.innerHTML = '<div class="tours-loading">Загружаем туры...</div>';

  try {
    const res = await fetch(`${API}/tours/popular?limit=6`);
    const tours = await res.json();
    container.innerHTML = '';

    if (!tours.length) {
      container.innerHTML = '<p class="no-tours">Туры скоро появятся!</p>';
      return;
    }

    tours.forEach(t => {
      const card = document.createElement('article');
      card.className = 'tour-card';
      card.innerHTML = `
        <div class="tour-card-body">
          <h3 class="tour-card-title">${t.name}</h3>
          <p class="tour-card-desc">${truncate(t.description, 120)}</p>
          <div class="tour-card-footer">
            <span class="tour-price">от ${Number(t.price).toLocaleString('ru-RU')} ₽/чел.</span>
            <a href="/tour/${t.id}" class="btn-tour-detail">Подробнее</a>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch {
    container.innerHTML = '<p class="tours-error">Не удалось загрузить туры. Попробуйте позже.</p>';
  }
}

async function loadArchivedTours() {
  const container = document.getElementById('archive-tours-grid');
  if (!container) return;

  try {
    const res = await fetch(`${API}/tours?archived=true`);
    const tours = await res.json();
    container.innerHTML = '';

    if (!tours.length) {
      container.innerHTML = '<p class="no-tours">Архивных туров пока нет.</p>';
      return;
    }

    tours.forEach(t => {
      const card = document.createElement('article');
      card.className = 'tour-card tour-card--archived';
      card.innerHTML = `
        <div class="tour-card-body">
          <span class="tour-archived-badge">Архив</span>
          <h3 class="tour-card-title">${t.name}</h3>
          <p class="tour-card-desc">${t.description || ''}</p>
          <div class="tour-card-footer">
            <span class="tour-price">от ${Number(t.price).toLocaleString('ru-RU')} ₽/чел.</span>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch {
    container.innerHTML = '<p class="tours-error">Не удалось загрузить архив.</p>';
  }
}

function initAnchorButton() {
  const btn = document.getElementById('go-btn');
  if (!btn) return;
  btn.addEventListener('click', e => {
    e.preventDefault();
    const target = document.getElementById('tours-section');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}

function applyRefCodeFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const ref = params.get('ref');
  if (ref) {
    sessionStorage.setItem('ref_code', ref);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  applyRefCodeFromUrl();
  loadPopularTours();
  initAnchorButton();

  const archiveSection = document.getElementById('archive-tours-grid');
  if (archiveSection) loadArchivedTours();
});
