const state = {
    theme: localStorage.getItem('theme') || 'dark',
    user: null,
    entryPoints: [],
    routes: [],
    charts: {},
    wizardStep: 1,
};

const selectors = {
    authScreen: () => document.getElementById('auth'),
    shell: () => document.getElementById('shell'),
    themeToggle: () => document.getElementById('themeToggle'),
    navItems: () => document.querySelectorAll('.nav-item'),
    pages: () => document.querySelectorAll('.page'),
    entryPointModal: () => document.getElementById('entryPointModal'),
    routeWizard: () => document.getElementById('routeWizard'),
    toastContainer: () => document.querySelector('.toast-container'),
};

const mockData = {
    entryPoints: [
        {
            id: 1,
            status: 'online',
            name: 'AMS-01',
            flag: '🇳🇱',
            location: 'Амстердам, Нидерланды',
            ip: '203.0.113.11',
            wgIp: '10.0.0.2',
            traffic: 72,
            cpu: 38,
            ram: 54,
            latency: 12,
            uptime: '34д 11ч',
            peers: 14,
        },
        {
            id: 2,
            status: 'online',
            name: 'FRA-01',
            flag: '🇩🇪',
            location: 'Франкфурт, Германия',
            ip: '198.51.100.20',
            wgIp: '10.0.0.3',
            traffic: 54,
            cpu: 24,
            ram: 43,
            latency: 19,
            uptime: '12д 03ч',
            peers: 13,
        },
        {
            id: 3,
            status: 'degraded',
            name: 'SIN-01',
            flag: '🇸🇬',
            location: 'Сингапур',
            ip: '203.0.113.76',
            wgIp: '10.0.0.9',
            traffic: 91,
            cpu: 72,
            ram: 71,
            latency: 211,
            uptime: '8д 19ч',
            peers: 14,
        },
        {
            id: 4,
            status: 'offline',
            name: 'SCL-01',
            flag: '🇨🇱',
            location: 'Сантьяго, Чили',
            ip: '203.0.113.90',
            wgIp: '10.0.0.15',
            traffic: 0,
            cpu: 0,
            ram: 0,
            latency: 0,
            uptime: '—',
            peers: 13,
        },
    ],
    routes: [
        {
            id: 1,
            status: 'active',
            subdomain: 'play.eu.example.com',
            client: '145.239.12.56:25565',
            protocol: 'TCP',
            haproxy: true,
            connections: 2345,
            traffic: '4.8 Гбит/с',
            latency: '43 мс',
            created: '12.04.2024',
        },
        {
            id: 2,
            status: 'paused',
            subdomain: 'fivem.na.example.com',
            client: '23.54.12.78:30120',
            protocol: 'UDP',
            haproxy: false,
            connections: 0,
            traffic: '0 Гбит/с',
            latency: '—',
            created: '28.03.2024',
        },
        {
            id: 3,
            status: 'error',
            subdomain: 'rust.asia.example.com',
            client: '13.248.91.11:28015',
            protocol: 'TCP+UDP',
            haproxy: true,
            connections: 562,
            traffic: '1.2 Гбит/с',
            latency: '182 мс',
            created: '04.05.2024',
        },
    ],
    alerts: [
        { id: 1, type: 'error', message: 'SCL-01 недоступен > 5 минут', timestamp: '2 мин назад' },
        { id: 2, type: 'warning', message: 'Высокий CPU на SIN-01', timestamp: '7 мин назад' },
        { id: 3, type: 'success', message: 'Маршрут play.eu.example.com обновлен', timestamp: '12 мин назад' },
    ],
    ddos: [
        { attack: 'SYN Flood', source: '45.134.22.1 (PL)', blocked: '2.3M', status: 'Смягчено' },
        { attack: 'UDP Amplification', source: '103.23.5.21 (CN)', blocked: '1.1M', status: 'Блокировано' },
        { attack: 'HTTP GET', source: '186.21.18.14 (BR)', blocked: '820K', status: 'Режим High' },
    ],
    metrics: [
        { name: 'Трафик', value: '182.4 Гбит/с', trend: '+12%' },
        { name: 'CPU среднее', value: '48%', trend: '+4%' },
        { name: 'Соединения', value: '12 482', trend: '+2%' },
        { name: 'Ошибки', value: '0.02%', trend: '-0.1%' },
    ],
    team: [
        { name: 'Алексей Игровой', role: 'Owner', email: 'alex@example.com' },
        { name: 'Мария Неткод', role: 'Admin', email: 'maria@example.com' },
        { name: 'Игорь DevOps', role: 'Viewer', email: 'igor@example.com' },
    ],
};

function initTheme() {
    if (state.theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', state.theme);
}

function showToast(message, type = 'success') {
    const container = selectors.toastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i data-lucide="${type === 'error' ? 'alert-triangle' : 'check-circle'}"></i><span>${message}</span>`;
    container.appendChild(toast);
    lucide.createIcons({ root: toast });
    setTimeout(() => toast.remove(), 5000);
}

function setupAuth() {
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');
    const forgotBtn = document.getElementById('forgotPasswordBtn');
    const forgotForm = document.getElementById('forgotPasswordForm');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.target).classList.add('active');
        });
    });

    forgotBtn.addEventListener('click', () => {
        forms.forEach(f => f.classList.remove('active'));
        forgotForm.classList.add('active');
    });

    forgotForm.querySelector('[data-action="backToLogin"]').addEventListener('click', () => {
        forgotForm.classList.remove('active');
        document.getElementById('loginForm').classList.add('active');
        document.querySelector('.auth-tab[data-target="loginForm"]').classList.add('active');
    });

    document.getElementById('loginForm').addEventListener('submit', event => {
        event.preventDefault();
        state.user = { email: event.target.email.value };
        selectors.authScreen().classList.remove('active');
        selectors.authScreen().classList.add('hidden');
        selectors.shell().classList.remove('hidden');
        showToast('Добро пожаловать обратно!', 'success');
    });

    document.getElementById('registerForm').addEventListener('submit', event => {
        event.preventDefault();
        const { password, confirmPassword } = event.target;
        if (password.value !== confirmPassword.value) {
            showToast('Пароли не совпадают', 'error');
            return;
        }
        showToast('Аккаунт создан! Проверьте почту для подтверждения.', 'success');
    });

    forgotForm.addEventListener('submit', event => {
        event.preventDefault();
        showToast('Ссылка для сброса отправлена на email', 'success');
    });
}

function switchSection(section) {
    selectors.navItems().forEach(item => item.classList.toggle('active', item.dataset.section === section));
    selectors.pages().forEach(page => page.classList.toggle('active', page.id === section));
    lucide.createIcons();
}

function setupNavigation() {
    selectors.navItems().forEach(item => {
        item.addEventListener('click', () => switchSection(item.dataset.section));
    });
}

function renderEntryPoints() {
    const tbody = document.getElementById('entryPointRows');
    tbody.innerHTML = '';
    state.entryPoints.forEach(ep => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="badge ${ep.status === 'online' ? 'success' : ep.status === 'degraded' ? 'warning' : 'danger'}">${ep.status}</span></td>
            <td>${ep.flag} ${ep.name}</td>
            <td>${ep.location}</td>
            <td><button class="link" data-copy="${ep.ip}">${ep.ip}</button></td>
            <td><button class="link" data-copy="${ep.wgIp}">${ep.wgIp}</button></td>
            <td>
                <div class="progress"><span style="width:${ep.traffic}%"></span></div>
                <small>${ep.traffic}%</small>
            </td>
            <td>${ep.cpu}%</td>
            <td>${ep.ram}%</td>
            <td>${ep.latency ? ep.latency + ' мс' : '—'}</td>
            <td>${ep.uptime}</td>
            <td>${ep.peers}</td>
            <td>
                <div class="actions">
                    <button class="icon-btn" title="Рестарт" data-action="restart" data-id="${ep.id}"><i data-lucide="refresh-ccw"></i></button>
                    <button class="icon-btn" title="Логи" data-action="logs" data-id="${ep.id}"><i data-lucide="file-text"></i></button>
                    <button class="icon-btn" title="Удалить" data-action="delete" data-id="${ep.id}"><i data-lucide="trash-2"></i></button>
                </div>
            </td>`;
        tbody.appendChild(tr);
    });
    lucide.createIcons({ root: tbody });

    tbody.querySelectorAll('[data-copy]').forEach(btn => {
        btn.addEventListener('click', () => {
            navigator.clipboard.writeText(btn.dataset.copy);
            showToast(`Скопировано: ${btn.dataset.copy}`);
        });
    });
}

function renderRoutes() {
    const tbody = document.getElementById('routeRows');
    tbody.innerHTML = '';
    state.routes.forEach(route => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="badge ${route.status === 'active' ? 'success' : route.status === 'paused' ? 'warning' : 'danger'}">${route.status}</span></td>
            <td>${route.subdomain}</td>
            <td>${route.client}</td>
            <td>${route.protocol}</td>
            <td>${route.haproxy ? 'Да' : 'Нет'}</td>
            <td>${route.connections.toLocaleString('ru-RU')}</td>
            <td>${route.traffic}</td>
            <td>${route.latency}</td>
            <td>${route.created}</td>
            <td>
                <div class="actions">
                    <button class="icon-btn" title="Пауза" data-action="pause" data-id="${route.id}"><i data-lucide="pause"></i></button>
                    <button class="icon-btn" title="Редактировать" data-action="edit" data-id="${route.id}"><i data-lucide="pencil"></i></button>
                    <button class="icon-btn" title="Удалить" data-action="delete" data-id="${route.id}"><i data-lucide="trash"></i></button>
                </div>
            </td>`;
        tbody.appendChild(tr);
    });
    lucide.createIcons({ root: tbody });
}

function renderAlerts() {
    const list = document.getElementById('alertsList');
    list.innerHTML = '';
    mockData.alerts.forEach(alert => {
        const div = document.createElement('div');
        div.className = `alert ${alert.type}`;
        div.innerHTML = `<strong>${alert.message}</strong><br /><small>${alert.timestamp}</small>`;
        list.appendChild(div);
    });
}

function renderDdosFeed() {
    const container = document.getElementById('ddosFeed');
    container.innerHTML = '';
    mockData.ddos.forEach(item => {
        const card = document.createElement('div');
        card.className = 'alert warning';
        card.innerHTML = `<strong>${item.attack}</strong><br /><small>${item.source}</small><br /><span>${item.blocked} пакетов • ${item.status}</span>`;
        container.appendChild(card);
    });
}

function renderMetrics() {
    const list = document.getElementById('liveMetrics');
    list.innerHTML = '';
    mockData.metrics.forEach(metric => {
        const item = document.createElement('li');
        item.innerHTML = `<span>${metric.name}</span><strong>${metric.value}</strong><small>${metric.trend}</small>`;
        list.appendChild(item);
    });
}

function renderTeam() {
    const list = document.getElementById('teamList');
    list.innerHTML = '';
    mockData.team.forEach(member => {
        const li = document.createElement('li');
        li.className = 'team-member';
        li.innerHTML = `<div><strong>${member.name}</strong><br /><small>${member.email}</small></div><span>${member.role}</span>`;
        list.appendChild(li);
    });
}

function createSparklines() {
    document.querySelectorAll('.sparkline').forEach(container => {
        const canvas = document.createElement('canvas');
        container.innerHTML = '';
        container.appendChild(canvas);
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 80);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.4)');
        gradient.addColorStop(1, 'rgba(118, 75, 162, 0.05)');
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: Array.from({ length: 12 }).map((_, i) => i + 1),
                datasets: [
                    {
                        data: Array.from({ length: 12 }).map(() => Math.random() * 100),
                        borderColor: '#8b5cf6',
                        backgroundColor: gradient,
                        tension: 0.45,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } },
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    });
}

function createCharts() {
    const trafficCtx = document.getElementById('trafficChart');
    state.charts.traffic = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: Array.from({ length: 12 }, (_, i) => `${i * 5} мин`),
            datasets: state.entryPoints.map((ep, index) => ({
                label: ep.name,
                data: Array.from({ length: 12 }).map(() => Math.random() * 150),
                borderColor: `hsl(${index * 60}, 80%, 60%)`,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
            })),
        },
        options: {
            plugins: { legend: { labels: { color: '#cbd5f5' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.15)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.15)' } },
            },
        },
    });

    const analyticsCharts = {
        trafficHistory: { type: 'line', data: () => Array.from({ length: 7 }).map(() => Math.random() * 200) },
        topRoutes: { type: 'bar', data: () => Array.from({ length: 5 }).map(() => Math.random() * 100) },
        countryDistribution: { type: 'doughnut', data: () => [35, 22, 18, 15, 10] },
        heatmap: { type: 'bar', data: () => Array.from({ length: 24 }).map(() => Math.random() * 100) },
        entryPointComparison: { type: 'line', data: () => Array.from({ length: 12 }).map(() => Math.random() * 150) },
    };

    Object.entries(analyticsCharts).forEach(([id, config]) => {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        state.charts[id] = new Chart(ctx, {
            type: config.type,
            data: {
                labels: Array.from({ length: config.type === 'doughnut' ? 5 : 12 }).map((_, i) => i + 1),
                datasets: [
                    {
                        data: config.data(),
                        backgroundColor: ['#8b5cf6', '#6366f1', '#0ea5e9', '#14b8a6', '#f97316', '#22c55e'],
                        borderColor: 'transparent',
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                plugins: { legend: { labels: { color: '#cbd5f5' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.08)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.08)' } },
                },
            },
        });
    });
}

function renderAnalyticsStats() {
    const stats = [
        { label: 'Total трафик (30д)', value: '2.4 ПБ' },
        { label: 'Уникальные IP', value: '1.2M' },
        { label: 'Среднее время сессии', value: '32 мин' },
        { label: 'Страны', value: '74' },
        { label: 'Платформы', value: 'PC 68%, Console 22%, Mobile 10%' },
    ];
    const container = document.getElementById('analyticsStats');
    container.innerHTML = '';
    stats.forEach(stat => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${stat.label}</span><strong>${stat.value}</strong>`;
        container.appendChild(li);
    });
}

function setupThemeToggle() {
    selectors.themeToggle().addEventListener('click', () => {
        toggleTheme();
        lucide.createIcons();
    });
}

function setupModals() {
    document.getElementById('addEntryPoint').addEventListener('click', () => openModal('entryPointModal'));
    document.getElementById('createRoute').addEventListener('click', () => openModal('routeWizard'));

    document.querySelectorAll('.modal [data-close]').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.closest('.modal').id));
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', event => {
            if (event.target === modal) closeModal(modal.id);
        });
    });
}

function openModal(id) {
    const modal = document.getElementById(id);
    modal.setAttribute('aria-hidden', 'false');
    lucide.createIcons({ root: modal });
}

function closeModal(id) {
    const modal = document.getElementById(id);
    modal.setAttribute('aria-hidden', 'true');
}

function setupEntryPointForm() {
    const form = document.getElementById('entryPointForm');
    const conditionalFields = form.querySelectorAll('.conditional');
    form.ssh_method.addEventListener('change', () => {
        conditionalFields.forEach(field => {
            field.style.display = field.dataset.method === form.ssh_method.value ? 'grid' : 'none';
        });
    });
    form.dispatchEvent(new Event('change'));

    form.addEventListener('submit', event => {
        event.preventDefault();
        form.classList.add('hidden');
        const installation = document.getElementById('installationProgress');
        installation.classList.remove('hidden');
        runInstallationWizard(installation.querySelector('.progress-list'), installation.querySelector('.log'));
    });
}

function runInstallationWizard(list, log) {
    const steps = [
        'Подключение по SSH',
        'Обновление системы',
        'Установка WireGuard',
        'Установка HAProxy',
        'Установка nftables',
        'Генерация ключей',
        'Настройка mesh-сети',
        'Добавление пиров',
        'Применение маршрутов',
        'Запуск сервисов',
    ];
    list.innerHTML = '';
    log.value = '';
    steps.forEach(step => {
        const li = document.createElement('li');
        li.className = 'progress-step';
        li.innerHTML = `<i data-lucide="loader"></i><span>${step}</span>`;
        list.appendChild(li);
    });
    lucide.createIcons({ root: list });

    steps.forEach((step, index) => {
        setTimeout(() => {
            const li = list.children[index];
            li.classList.add('completed');
            li.innerHTML = `<i data-lucide="check"></i><span>${step}</span>`;
            log.value += `[${new Date().toLocaleTimeString()}] ${step} — успешно\n`;
            log.scrollTop = log.scrollHeight;
            lucide.createIcons({ root: li });
            if (index === steps.length - 1) {
                showToast('Entry Point успешно установлен');
                closeModal('entryPointModal');
                document.getElementById('entryPointForm').classList.remove('hidden');
                document.getElementById('installationProgress').classList.add('hidden');
            }
        }, 1000 * (index + 1));
    });
}

function setupRouteWizard() {
    const wizard = document.getElementById('routeWizard');
    const steps = wizard.querySelectorAll('.wizard-steps .step');
    const sections = wizard.querySelectorAll('.wizard-step');
    const nextBtn = wizard.querySelector('[data-action="next"]');
    const prevBtn = wizard.querySelector('[data-action="prev"]');

    function updateWizard(step) {
        state.wizardStep = step;
        steps.forEach(btn => btn.classList.toggle('active', Number(btn.dataset.step) === step));
        sections.forEach(section => section.classList.toggle('active', Number(section.dataset.step) === step));
        prevBtn.disabled = step === 1;
        nextBtn.textContent = step === steps.length ? 'Готово' : 'Далее';
        if (step === 5) {
            populateRouteSummary();
        }
    }

    nextBtn.addEventListener('click', () => {
        if (state.wizardStep < steps.length) {
            updateWizard(state.wizardStep + 1);
        } else {
            document.getElementById('routeForm').dispatchEvent(new Event('submit'));
        }
    });

    prevBtn.addEventListener('click', () => {
        if (state.wizardStep > 1) updateWizard(state.wizardStep - 1);
    });

    steps.forEach(btn => btn.addEventListener('click', () => updateWizard(Number(btn.dataset.step))));

    document.getElementById('routeForm').addEventListener('submit', event => {
        event.preventDefault();
        showToast('Маршрут создан и распространяется на Entry Points');
        closeModal('routeWizard');
        updateWizard(1);
    });

    document.getElementById('checkDns').addEventListener('click', () => showToast('DNS записи обнаружены. SRV и A настроены корректно.'));
    document.getElementById('copyDns').addEventListener('click', () => {
        navigator.clipboard.writeText('_game._tcp.play.example.com 5 0 25565 entry.anycast.net');
        showToast('DNS инструкции скопированы в буфер');
    });
    document.getElementById('probeServer').addEventListener('click', () => showToast('Успешное подключение к клиентскому серверу. Определено: Minecraft.'));

    const selector = document.getElementById('entryPointSelector');
    selector.innerHTML = '';
    state.entryPoints.forEach(ep => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'selector-item active';
        item.dataset.id = ep.id;
        item.innerHTML = `<strong>${ep.name}</strong><span>${ep.location}</span>`;
        item.addEventListener('click', () => {
            item.classList.toggle('active');
        });
        selector.appendChild(item);
    });

    updateWizard(1);
}

function populateRouteSummary() {
    const form = document.getElementById('routeForm');
    const summary = document.getElementById('routeSummary');
    const selectedEntryPoints = Array.from(document.querySelectorAll('#entryPointSelector .selector-item.active')).map(item => item.querySelector('strong').textContent);
    summary.innerHTML = `
        <div><strong>Поддомен</strong><p>${form.subdomain.value || '—'}</p></div>
        <div><strong>Клиент</strong><p>${form.client_ip.value}:${form.client_port.value}</p></div>
        <div><strong>Протокол</strong><p>${form.protocol.value}</p></div>
        <div><strong>HAProxy</strong><p>${form.haproxy.checked ? 'Включен (PROXY v2)' : 'Выключен'}</p></div>
        <div><strong>Балансировка</strong><p>${form.balancing.value}</p></div>
        <div><strong>DDoS</strong><p>${form.ddos.value}</p></div>
        <div><strong>Rate limit</strong><p>${form.rate.value || '—'}</p></div>
        <div><strong>Entry Points</strong><p>${selectedEntryPoints.join(', ') || 'Все'}</p></div>
    `;
}

function setupProfileMenu() {
    const menu = document.getElementById('profileMenu');
    const button = document.getElementById('profileMenuBtn');
    button.addEventListener('click', event => {
        event.stopPropagation();
        const rect = button.getBoundingClientRect();
        menu.style.top = `${rect.bottom + window.scrollY + 8}px`;
        menu.style.left = `${rect.right - 200}px`;
        const isHidden = menu.getAttribute('aria-hidden') !== 'false';
        menu.setAttribute('aria-hidden', isHidden ? 'false' : 'true');
    });
    document.addEventListener('click', event => {
        if (!menu.contains(event.target) && event.target !== button) {
            menu.setAttribute('aria-hidden', 'true');
        }
    });
    menu.querySelector('[data-action="logout"]').addEventListener('click', () => {
        selectors.shell().classList.add('hidden');
        selectors.authScreen().classList.remove('hidden');
        selectors.authScreen().classList.add('active');
        menu.setAttribute('aria-hidden', 'true');
        showToast('Вы вышли из аккаунта', 'success');
    });
    menu.querySelector('[data-action="settings"]').addEventListener('click', () => switchSection('settings'));
}

function drawMap() {
    const canvas = document.getElementById('mapCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'rgba(148, 163, 184, 0.1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const points = [
        { x: 180, y: 140, label: 'AMS-01', load: 0.3 },
        { x: 220, y: 160, label: 'FRA-01', load: 0.28 },
        { x: 680, y: 200, label: 'SIN-01', load: 0.76 },
        { x: 120, y: 280, label: 'SCL-01', load: 0.1 },
        { x: 360, y: 120, label: 'NYC-01', load: 0.55 },
    ];

    ctx.strokeStyle = 'rgba(102, 126, 234, 0.35)';
    ctx.lineWidth = 2;
    points.forEach((source, i) => {
        points.slice(i + 1).forEach(target => {
            ctx.beginPath();
            ctx.moveTo(source.x, source.y);
            ctx.lineTo(target.x, target.y);
            ctx.stroke();
        });
    });

    points.forEach(point => {
        const color = point.load > 0.7 ? '#f87171' : point.load > 0.5 ? '#fbbf24' : '#34d399';
        ctx.beginPath();
        ctx.fillStyle = color;
        ctx.arc(point.x, point.y, 10 + point.load * 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '14px Inter';
        ctx.fillText(point.label, point.x + 16, point.y + 4);
    });
}

function updateLiveData() {
    const trafficEl = document.getElementById('trafficTotal');
    const connectionsEl = document.getElementById('connectionsTotal');
    const ddosEl = document.getElementById('ddosBlocked');

    setInterval(() => {
        const traffic = (180 + Math.random() * 10).toFixed(1);
        const connections = Math.floor(12400 + Math.random() * 400);
        const ddos = 320 + Math.floor(Math.random() * 20);
        trafficEl.textContent = traffic;
        connectionsEl.textContent = connections.toLocaleString('ru-RU');
        ddosEl.textContent = ddos.toLocaleString('ru-RU');
        if (state.charts.traffic) {
            state.charts.traffic.data.datasets.forEach(dataset => {
                dataset.data.shift();
                dataset.data.push(Math.random() * 150);
            });
            state.charts.traffic.update('none');
        }
    }, 3000);
}

function registerHotkeys() {
    window.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
            event.preventDefault();
            showToast('Командная палитра пока в разработке', 'success');
        }
    });
}

function initPwaButton() {
    const btn = document.getElementById('pwaInstall');
    btn.addEventListener('click', () => showToast('Добавьте панель на главный экран через меню браузера.'));
}

function init() {
    initTheme();
    lucide.createIcons();
    selectors.shell().classList.add('hidden');
    selectors.authScreen().classList.add('active');
    selectors.authScreen().classList.remove('hidden');

    state.entryPoints = mockData.entryPoints;
    state.routes = mockData.routes;

    setupAuth();
    setupNavigation();
    setupThemeToggle();
    setupModals();
    setupEntryPointForm();
    setupRouteWizard();
    setupProfileMenu();
    registerHotkeys();
    initPwaButton();

    renderEntryPoints();
    renderRoutes();
    renderAlerts();
    renderDdosFeed();
    renderMetrics();
    renderTeam();
    renderAnalyticsStats();
    createSparklines();
    createCharts();
    drawMap();
    updateLiveData();
}

document.addEventListener('DOMContentLoaded', init);
