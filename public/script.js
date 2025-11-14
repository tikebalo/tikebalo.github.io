const API_BASE = '/api';
let accessToken = localStorage.getItem('anycast_token');
let currentUser = null;
let entryPoints = [];
let routes = [];

const elements = {
  authView: document.getElementById('authView'),
  dashboard: document.getElementById('dashboard'),
  loginForm: document.getElementById('loginForm'),
  registerForm: document.getElementById('registerForm'),
  loginTab: document.getElementById('loginTab'),
  registerTab: document.getElementById('registerTab'),
  userEmail: document.getElementById('userEmail'),
  refreshBtn: document.getElementById('refreshBtn'),
  logoutBtn: document.getElementById('logoutBtn'),
  entryPointTableBody: document.querySelector('#entryPointTable tbody'),
  routeTableBody: document.querySelector('#routeTable tbody'),
  entryPointForm: document.getElementById('entryPointForm'),
  routeForm: document.getElementById('routeForm'),
  routeEntryPoints: document.getElementById('routeEntryPoints'),
  toast: document.getElementById('toast'),
  statEntryPoints: document.getElementById('statEntryPoints'),
  statRoutes: document.getElementById('statRoutes'),
  statProxy: document.getElementById('statProxy'),
  statUdp: document.getElementById('statUdp'),
  overlay: document.getElementById('loadingOverlay'),
  overlayMessage: document.getElementById('overlayMessage'),
};

function setToken(token) {
  accessToken = token;
  if (token) {
    localStorage.setItem('anycast_token', token);
  } else {
    localStorage.removeItem('anycast_token');
  }
}

async function api(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    setToken(null);
    showAuth();
    throw new Error('Необходима авторизация');
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || 'Ошибка запроса');
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.remove('hidden');
  requestAnimationFrame(() => {
    elements.toast.classList.add('show');
  });
  setTimeout(() => {
    elements.toast.classList.remove('show');
    setTimeout(() => elements.toast.classList.add('hidden'), 250);
  }, 2600);
}

function showAuth() {
  currentUser = null;
  elements.dashboard.classList.add('hidden');
  elements.authView.classList.remove('hidden');
  setLoading(false);
}

function showDashboard() {
  elements.authView.classList.add('hidden');
  elements.dashboard.classList.remove('hidden');
}

function setLoading(isLoading, message = 'Обновление данных…') {
  if (!elements.overlay) return;
  if (message) {
    elements.overlayMessage.textContent = message;
  }
  if (isLoading) {
    elements.overlay.classList.remove('hidden');
  } else {
    elements.overlay.classList.add('hidden');
  }
}

function switchTab(target) {
  if (target === 'login') {
    elements.loginTab.classList.add('active');
    elements.registerTab.classList.remove('active');
    elements.loginForm.classList.remove('hidden');
    elements.registerForm.classList.add('hidden');
  } else {
    elements.registerTab.classList.add('active');
    elements.loginTab.classList.remove('active');
    elements.registerForm.classList.remove('hidden');
    elements.loginForm.classList.add('hidden');
  }
}

async function restoreSession() {
  if (!accessToken) {
    showAuth();
    return;
  }

  try {
    setLoading(true, 'Проверяем сессию…');
    currentUser = await api('/auth/me');
    elements.userEmail.textContent = currentUser.email;
    showDashboard();
    await loadData();
  } catch (error) {
    console.warn('Unable to restore session', error);
    setToken(null);
    showAuth();
  }
}

async function loadData() {
  try {
    setLoading(true);
    const [entryPointResponse, routeResponse] = await Promise.all([
      api('/entry-points'),
      api('/routes'),
    ]);
    entryPoints = entryPointResponse;
    routes = routeResponse;
    renderEntryPoints();
    renderRoutes();
    updateStats();
  } finally {
    setLoading(false);
  }
}

function renderEntryPoints() {
  elements.entryPointTableBody.innerHTML = '';
  elements.routeEntryPoints.innerHTML = '';

  entryPoints.forEach((entryPoint) => {
    const tr = document.createElement('tr');
    const normalizedStatus = entryPoint.status ? entryPoint.status.toLowerCase() : 'online';
    const statusClass = ['online', 'maintenance', 'offline'].includes(normalizedStatus)
      ? normalizedStatus
      : 'online';
    tr.innerHTML = `
      <td>${entryPoint.name}</td>
      <td>${entryPoint.location}</td>
      <td>${entryPoint.ip}</td>
      <td><span class="status-chip status-${statusClass}">${entryPoint.status}</span></td>
      <td><button class="action-button" data-id="${entryPoint.id}">Удалить</button></td>
    `;
    tr.querySelector('button').addEventListener('click', () => deleteEntryPoint(entryPoint.id));
    elements.entryPointTableBody.appendChild(tr);

    const option = document.createElement('option');
    option.value = entryPoint.id;
    option.textContent = `${entryPoint.name} · ${entryPoint.location}`;
    elements.routeEntryPoints.appendChild(option);
  });
}

function renderRoutes() {
  elements.routeTableBody.innerHTML = '';

  routes.forEach((route) => {
    const entryPointLabels = route.entry_points
      .map((id) => entryPoints.find((entry) => entry.id === id))
      .filter(Boolean)
      .map((entry) => entry.name)
      .join(', ');

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${route.subdomain}</td>
      <td>${route.client_ip}:${route.client_port}</td>
      <td>${route.protocol.toUpperCase()}${route.use_haproxy ? ' + HAProxy' : ''}</td>
      <td>${entryPointLabels || '—'}</td>
      <td><button class="action-button" data-id="${route.id}">Удалить</button></td>
    `;
    tr.querySelector('button').addEventListener('click', () => deleteRoute(route.id));
    elements.routeTableBody.appendChild(tr);
  });
}

function updateStats() {
  if (!elements.statEntryPoints) return;
  const proxyCount = routes.filter((route) => route.use_haproxy && route.protocol.includes('tcp')).length;
  const udpCount = routes.filter((route) => route.protocol.includes('udp')).length;

  elements.statEntryPoints.textContent = entryPoints.length.toString();
  elements.statRoutes.textContent = routes.length.toString();
  elements.statProxy.textContent = proxyCount.toString();
  elements.statUdp.textContent = udpCount.toString();
}

async function deleteEntryPoint(id) {
  try {
    await api(`/entry-points/${id}`, { method: 'DELETE' });
    entryPoints = entryPoints.filter((entry) => entry.id !== id);
    routes = routes.map((route) => ({
      ...route,
      entry_points: route.entry_points.filter((entryId) => entryId !== id),
    }));
    renderEntryPoints();
    renderRoutes();
    updateStats();
    showToast('Entry point удалён');
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteRoute(id) {
  try {
    await api(`/routes/${id}`, { method: 'DELETE' });
    routes = routes.filter((route) => route.id !== id);
    renderRoutes();
    updateStats();
    showToast('Маршрут удалён');
  } catch (error) {
    showToast(error.message);
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setToken(data.access_token);
    currentUser = await api('/auth/me');
    elements.userEmail.textContent = currentUser.email;
    showDashboard();
    event.currentTarget.reset();
    await loadData();
    showToast('Добро пожаловать!');
  } catch (error) {
    showToast(error.message);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    await api('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast('Аккаунт создан. Теперь войдите.');
    switchTab('login');
    event.currentTarget.reset();
  } catch (error) {
    showToast(error.message);
  }
}

async function handleEntryPointCreate(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  payload.ssh_port = Number(payload.ssh_port);

  try {
    const entryPoint = await api('/entry-points', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    entryPoints = [entryPoint, ...entryPoints];
    renderEntryPoints();
    updateStats();
    event.currentTarget.reset();
    event.currentTarget.querySelector('[name="ssh_port"]').value = '22';
    showToast('Entry point создан');
  } catch (error) {
    showToast(error.message);
  }
}

async function handleRouteCreate(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  payload.client_port = Number(payload.client_port);
  payload.use_haproxy = formData.get('use_haproxy') === 'on';
  payload.entry_points = Array.from(elements.routeEntryPoints.selectedOptions).map((option) => Number(option.value));

  try {
    const route = await api('/routes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    routes = [route, ...routes];
    renderRoutes();
    updateStats();
    event.currentTarget.reset();
    elements.routeEntryPoints.selectedIndex = -1;
    const haproxyToggle = event.currentTarget.querySelector('[name="use_haproxy"]');
    if (haproxyToggle) {
      haproxyToggle.checked = true;
    }
    showToast('Маршрут создан');
  } catch (error) {
    showToast(error.message);
  }
}

elements.loginForm.addEventListener('submit', handleLogin);
elements.registerForm.addEventListener('submit', handleRegister);
elements.entryPointForm.addEventListener('submit', handleEntryPointCreate);
elements.routeForm.addEventListener('submit', handleRouteCreate);
elements.logoutBtn.addEventListener('click', () => {
  setToken(null);
  entryPoints = [];
  routes = [];
  updateStats();
  showAuth();
});

if (elements.refreshBtn) {
  elements.refreshBtn.addEventListener('click', () => {
    loadData().then(() => showToast('Данные обновлены')).catch((error) => showToast(error.message));
  });
}

elements.loginTab.addEventListener('click', () => switchTab('login'));
elements.registerTab.addEventListener('click', () => switchTab('register'));

restoreSession();
