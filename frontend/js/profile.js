const API = '/api';

async function loadProfile() {
  const res = await fetch(`${API}/profile`);
  if (res.status === 401) {
    window.location.href = '/login';
    return;
  }
  const data = await res.json();
  renderProfile(data);
}

function renderProfile(data) {
  document.getElementById('profile-name').textContent = data.name;
  document.getElementById('profile-email').textContent = data.email;

  renderAchievements(data.achievements);
  renderBookingTabs(data.bookings, data.achievements);
  renderReferral(data.referral_link, data.ref_code);
}

function renderAchievements(achievements) {
  const grid = document.getElementById('achievements-grid');
  grid.innerHTML = '';
  achievements.forEach(ach => {
    const div = document.createElement('div');
    div.className = `achievement-card${ach.unlocked ? ' unlocked' : ' locked'}`;
    div.title = ach.description;
    div.innerHTML = `
      <span class="ach-icon">${ach.icon}</span>
      <span class="ach-name">${ach.name}</span>
      ${ach.unlocked ? '<span class="ach-check">✓</span>' : '<span class="ach-lock">🔒</span>'}
    `;
    grid.appendChild(div);
  });
}

function renderBookingTabs(bookings, achievements) {
  const tabs = ['booked', 'in_progress', 'completed'];
  const labels = { booked: 'Забронированные', in_progress: 'В процессе', completed: 'Завершённые' };

  const tabBar = document.getElementById('booking-tabs');
  const content = document.getElementById('booking-content');
  tabBar.innerHTML = '';

  tabs.forEach((tab, idx) => {
    const btn = document.createElement('button');
    btn.className = `tab-btn${idx === 0 ? ' active' : ''}`;
    btn.textContent = `${labels[tab]} (${bookings[tab].length})`;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderBookingList(bookings[tab], content);
    });
    tabBar.appendChild(btn);
  });

  renderBookingList(bookings.booked, content);
}

function renderBookingList(list, container) {
  container.innerHTML = '';
  if (!list.length) {
    container.innerHTML = '<p class="no-bookings">Туров в этой категории пока нет.</p>';
    return;
  }
  list.forEach(b => {
    const card = document.createElement('div');
    card.className = 'booking-card';
    const achHtml = b.achievements.length
      ? `<div class="booking-achievements">
          ${b.achievements.map(a => `<span class="ba-icon" title="${a.name}">${a.icon}</span>`).join('')}
        </div>`
      : '';
    card.innerHTML = `
      <div class="booking-info">
        <h4 class="booking-name">${b.tour_name}</h4>
        ${b.tour_date ? `<span class="booking-date">📅 ${formatDate(b.tour_date)}</span>` : ''}
        ${b.price ? `<span class="booking-price">💳 ${Number(b.price).toLocaleString('ru-RU')} ₽</span>` : ''}
      </div>
      ${achHtml}
    `;
    container.appendChild(card);
  });
}

function renderReferral(link, code) {
  const input = document.getElementById('referral-link');
  if (input) input.value = link;
  const codeEl = document.getElementById('referral-code');
  if (codeEl) codeEl.textContent = code;
}

function copyReferral() {
  const input = document.getElementById('referral-link');
  if (!input) return;
  input.select();
  document.execCommand('copy');
  const btn = document.getElementById('copy-ref-btn');
  if (btn) {
    btn.textContent = 'Скопировано!';
    setTimeout(() => { btn.textContent = 'Скопировать'; }, 2000);
  }
}

async function logout() {
  await fetch(`${API}/logout`, { method: 'POST' });
  window.location.href = '/';
}

function formatDate(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

document.addEventListener('DOMContentLoaded', () => {
  loadProfile();

  const copyBtn = document.getElementById('copy-ref-btn');
  if (copyBtn) copyBtn.addEventListener('click', copyReferral);

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
