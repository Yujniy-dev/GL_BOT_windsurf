const API = window.location.origin;
const user = Telegram.WebApp.initDataUnsafe.user || {};

async function loadTournamentInfo() {
    try {
        const r = await fetch(`${API}/api/tournament`);
        const d = await r.json();
        const el = document.getElementById('info');
        if (d.exists) el.innerHTML = `<p><strong>${d.name}</strong><br>Статус: ${d.status}<br>Участников: ${d.participants_count}/${d.max_participants}</p>`;
        else el.innerHTML = '<p>Нет активных турниров.</p>';
    } catch(e){ console.error(e); }
}

function showTab(id) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById('tab-' + id).style.display = 'block';
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');
}

async function loadApp() {
    loadTournamentInfo();
    loadStandings();
    loadMyMatches();
    loadRemaining();
}

async function loadStandings() {
    try {
        const r = await fetch(`${API}/api/standings`);
        const d = await r.json();
        const el = document.getElementById('tab-standings');
        if (!d.exists) { el.innerHTML = '<p>Нет данных.</p>'; return; }
        let html = `<h2>${d.tournament_name}</h2>`;
        d.groups.forEach(g => {
            html += `<h3>${g.group_name}</h3><table class="table"><thead><tr><th>#</th><th>Игрок</th><th>И</th><th>В</th><th>Н</th><th>П</th><th>ГЗ</th><th>ГП</th><th>РМ</th><th>О</th></tr></thead><tbody>`;
            g.standings.forEach((p,i) => {
                html += `<tr><td>${i+1}</td><td>${p.nickname}</td><td>${p.matches}</td><td>${p.wins}</td><td>${p.draws}</td><td>${p.losses}</td><td>${p.gf}</td><td>${p.ga}</td><td>${p.gd}</td><td><b>${p.points}</b></td></tr>`;
            });
            html += '</tbody></table>';
        });
        el.innerHTML = html;
    } catch(e){ console.error(e); }
}

async function loadMyMatches() {
    try {
        const r = await fetch(`${API}/api/my_matches?user_id=${user.id || 0}`);
        const d = await r.json();
        const el = document.getElementById('tab-my');
        if (!d.exists || !d.matches.length) { el.innerHTML = '<p>Нет матчей.</p>'; return; }
        let html = '<h3>Мои матчи</h3>';
        d.matches.forEach(m => {
            const status = m.finished ? `✅ ${m.my_score}:${m.opponent_score}` : '⏳ Не сыгран';
            html += `<div class="match">${m.opponent} — ${status}</div>`;
        });
        el.innerHTML = html;
    } catch(e){ console.error(e); }
}

async function loadRemaining() {
    try {
        const r = await fetch(`${API}/api/remaining?user_id=${user.id || 0}`);
        const d = await r.json();
        const el = document.getElementById('tab-remaining');
        if (!d.exists || !d.matches.length) { el.innerHTML = '<p>Все матчи сыграны!</p>'; return; }
        let html = '<h3>Осталось сыграть</h3>';
        d.matches.forEach(m => {
            html += `<div class="match">${m.opponent_nickname} (@${m.opponent_username}) <button onclick="openResult(${m.match_id}, '${m.opponent_nickname}')">Ввести результат</button></div>`;
        });
        el.innerHTML = html;
    } catch(e){ console.error(e); }
}

function openResult(id, opp) {
    document.getElementById('result-form').style.display = 'block';
    document.getElementById('matchId').value = id;
    document.getElementById('res-players').innerHTML = `<p>Матч против: <b>${opp}</b></p>`;
    document.getElementById('myScore').value = '';
    document.getElementById('oppScore').value = '';
}

function cancelResult() {
    document.getElementById('result-form').style.display = 'none';
}

async function submitMatchResult() {
    const id = document.getElementById('matchId').value;
    const s1 = parseInt(document.getElementById('myScore').value);
    const s2 = parseInt(document.getElementById('oppScore').value);
    if (isNaN(s1) || isNaN(s2)) return alert('Введи счет');
    if (s1 === s2) return alert('Ничья недопустима');
    try {
        const r = await fetch(`${API}/api/submit_result`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({match_id: parseInt(id), player1_score: s1, player2_score: s2, user_id: user.id || 0})
        });
        const d = await r.json();
        if (d.success) {
            alert('Сохранено!');
            cancelResult();
            loadMyMatches(); loadRemaining(); loadStandings();
        } else alert('Ошибка: ' + (d.error || ''));
    } catch(e){ alert('Сетевая ошибка'); }
}
