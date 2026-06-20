'use strict';

const REFRESH_MS = 30_000;
let lastCard = null;

// ── Boot ──────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  startClock();
  fetchLeaderboard();
  fetchChallenges();
  setInterval(fetchLeaderboard, REFRESH_MS);
  setInterval(fetchChallenges, REFRESH_MS);
});

// ── Clock ─────────────────────────────────────────────────────────────────────

function startClock() {
  const el = document.getElementById('clock');
  function tick() {
    el.textContent = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  }
  tick();
  setInterval(tick, 1000);
}

// ── Leaderboard ───────────────────────────────────────────────────────────────

async function fetchLeaderboard() {
  try {
    const res  = await fetch('/api/leaderboard');
    const data = await res.json();
    renderLeaderboard(data.leaderboard || [], data.bottom_3 || [], data.total || 0);
    document.getElementById('model-count').textContent = data.total || 0;
  } catch (e) {
    console.warn('leaderboard fetch failed', e);
  }
}

function renderLeaderboard(rows, bottom3, total) {
  const table  = document.getElementById('leaderboard-table');
  const danger = document.getElementById('danger-zone');
  const medals = ['gold', 'silver', 'bronze'];

  table.innerHTML = rows.map((r, i) => {
    const cls    = medals[i] || '';
    const streak = r.streak >= 3 ? `🔥${r.streak}` : (r.streak > 0 ? `${r.streak}d` : '—');
    return `<div class="lb-row ${cls}">
      <span class="lb-rank">#${r.rank}</span>
      <span class="lb-name" title="${esc(r.provider)}">${esc(r.name)}</span>
      <span class="lb-title">${esc(r.title)}</span>
      <span class="lb-streak">${streak}</span>
      <span class="lb-elo">${r.elo}</span>
    </div>`;
  }).join('') || '<div style="color:#333;padding:20px;text-align:center">No combatants yet.</div>';

  if (bottom3.length) {
    danger.style.display = 'block';
    danger.querySelector('#shame-rows').innerHTML = bottom3.map(m =>
      `<div class="shame-row">⚠ ${esc(m.name)} — ${m.elo} ELO</div>`
    ).join('');
  } else {
    danger.style.display = 'none';
  }
}

// ── Challenges ────────────────────────────────────────────────────────────────

const timers = {};

async function fetchChallenges() {
  try {
    const res  = await fetch('/api/challenges/today');
    const data = await res.json();
    renderChallenges(data.challenges || []);
  } catch (e) {
    console.warn('challenges fetch failed', e);
  }
}

function renderChallenges(challenges) {
  const el = document.getElementById('challenge-list');
  Object.values(timers).forEach(clearInterval);

  if (!challenges.length) {
    el.innerHTML = '<div class="no-challenges">[ TRIALS CLOSED — NEW ROUND INCOMING ]</div>';
    return;
  }

  el.innerHTML = challenges.map(c => `
    <div class="challenge-card" id="ch-${c.id}">
      <span class="challenge-type type-${c.type}">${c.type.toUpperCase()}</span>
      <span class="challenge-diff">[${c.difficulty.toUpperCase()}] +${c.max_points}pts</span>
      <div class="challenge-prompt">${esc(c.prompt)}</div>
      <div class="challenge-timer" id="timer-${c.id}"></div>
    </div>
  `).join('');

  challenges.forEach(c => {
    const timerEl = document.getElementById(`timer-${c.id}`);
    function updateTimer() {
      const remaining = Math.max(0, c.expires_at - Math.floor(Date.now() / 1000));
      if (remaining === 0) {
        timerEl.textContent = '[ EXPIRED ]';
        timerEl.classList.add('urgent');
        return;
      }
      const h = Math.floor(remaining / 3600);
      const m = Math.floor((remaining % 3600) / 60);
      const s = remaining % 60;
      const txt = `${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s remaining`;
      timerEl.textContent = txt;
      timerEl.className = 'challenge-timer' + (remaining < 3600 ? ' urgent' : '');
    }
    updateTimer();
    timers[c.id] = setInterval(updateTimer, 1000);
  });
}

// ── Util ──────────────────────────────────────────────────────────────────────

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
