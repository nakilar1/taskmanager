// Task Manager Frontend - Fixed Version
const API_URL = window.location.origin;

// State
let projects = [];
let tasks = [];

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const toastContainer = document.getElementById('toast-container');

// API Helper
async function api(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        },
        ...options
    };

    const res = await fetch(`${API_URL}/api${endpoint}`, config);
    const data = await res.json();

    if (!res.ok) {
        if (res.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            showAuth();
            throw new Error('AUTH_REQUIRED');
        }
        throw new Error(data.error || 'Ошибка сервера');
    }
    return data;
}

// Toast
function toast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    toastContainer.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

// Auth Functions
async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const data = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        showDashboard();
        toast('Добро пожаловать!', 'success');
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') {
            toast(err.message, 'error');
        }
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        
        toast('Регистрация успешна! Войдите.', 'success');
        showLogin();
    } catch (err) {
        toast(err.message, 'error');
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showAuth();
    toast('Вы вышли из системы', 'info');
}

// UI Functions
function showAuth() {
    authSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
}

async function showDashboard() {
    authSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    document.getElementById('current-user').textContent = user.username || 'User';

    await Promise.all([loadProjects(), loadTasks()]);
}

function showLogin() {
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('register-form').classList.add('hidden');
}

function showRegister() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
}

// Modal Functions
function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// Stats
function updateStats() {
    const inProgress = tasks.filter(t => t.status === 'in_progress').length;
    const done = tasks.filter(t => t.status === 'done').length;
    
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    
    setVal('stat-projects', projects.length);
    setVal('stat-tasks', tasks.length);
    setVal('stat-inprogress', inProgress);
    setVal('stat-done', done);
}

// Projects
async function loadProjects() {
    try {
        const data = await api('/projects');
        projects = data.projects || [];
        renderProjects();
        updateSelects();
        updateStats();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast('Ошибка загрузки проектов', 'error');
    }
}

function renderProjects() {
    const list = document.getElementById('projects-list');
    
    if (!projects.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📁</div><p>Нет проектов</p></div>';
        return;
    }

    list.innerHTML = projects.map(p => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">${esc(p.name)}</div>
                <div class="card-actions">
                    <button class="btn btn-small btn-secondary" onclick="editProject(${p.id})">✏️</button>
                    <button class="btn btn-small btn-danger" onclick="deleteProject(${p.id})">🗑️</button>
                </div>
            </div>
            <div class="card-description">${esc(p.description || 'Нет описания')}</div>
            <div class="card-meta">${fmtDate(p.created_at)}</div>
        </div>
    `).join('');
}

async function saveProject(e) {
    e.preventDefault();
    
    const id = document.getElementById('project-id').value;
    const name = document.getElementById('project-name').value;
    const desc = document.getElementById('project-desc').value;

    try {
        if (id) {
            await api(`/projects/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ name, description: desc })
            });
            toast('Проект обновлен', 'success');
        } else {
            await api('/projects', {
                method: 'POST',
                body: JSON.stringify({ name, description: desc })
            });
            toast('Проект создан', 'success');
        }
        
        closeModal('project-modal');
        loadProjects();
        e.target.reset();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast(err.message, 'error');
    }
}

function editProject(id) {
    const p = projects.find(x => x.id === id);
    if (!p) return;
    
    document.getElementById('project-id').value = p.id;
    document.getElementById('project-name').value = p.name;
    document.getElementById('project-desc').value = p.description || '';
    document.getElementById('project-modal-title').textContent = 'Редактировать проект';
    openModal('project-modal');
}

async function deleteProject(id) {
    if (!confirm('Удалить проект?')) return;
    
    try {
        await api(`/projects/${id}`, { method: 'DELETE' });
        toast('Проект удален', 'success');
        loadProjects();
        loadTasks();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast(err.message, 'error');
    }
}

// Tasks
async function loadTasks() {
    try {
        const projectFilter = document.getElementById('project-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        let url = '/tasks?';
        if (projectFilter) url += `project_id=${projectFilter}&`;
        if (statusFilter) url += `status=${statusFilter}`;

        const data = await api(url);
        tasks = data.tasks || [];
        renderTasks();
        updateStats();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast('Ошибка загрузки задач', 'error');
    }
}

function renderTasks() {
    const list = document.getElementById('tasks-list');
    
    if (!tasks.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p>Нет задач</p></div>';
        return;
    }

    list.innerHTML = tasks.map(t => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">${esc(t.title)}</div>
                <div>
                    <span class="badge status-${t.status}">${statusLabel(t.status)}</span>
                    <span class="badge priority-${t.priority}">${priorityLabel(t.priority)}</span>
                </div>
            </div>
            <div class="card-description">${esc(t.description || 'Нет описания')}</div>
            <div class="card-meta">
                <span>${getProjectName(t.project_id)}</span>
                <div class="card-actions">
                    <button class="btn btn-small btn-secondary" onclick="editTask(${t.id})">✏️</button>
                    <button class="btn btn-small btn-secondary" onclick="showComments(${t.id})">💬</button>
                    <button class="btn btn-small btn-danger" onclick="deleteTask(${t.id})">🗑️</button>
                </div>
            </div>
        </div>
    `).join('');
}

async function saveTask(e) {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const data = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-desc').value,
        project_id: parseInt(document.getElementById('task-project').value),
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value
    };

    try {
        if (id) {
            await api(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) });
            toast('Задача обновлена', 'success');
        } else {
            await api('/tasks', { method: 'POST', body: JSON.stringify(data) });
            toast('Задача создана', 'success');
        }
        
        closeModal('task-modal');
        loadTasks();
        e.target.reset();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast(err.message, 'error');
    }
}

function editTask(id) {
    const t = tasks.find(x => x.id === id);
    if (!t) return;
    
    document.getElementById('task-id').value = t.id;
    document.getElementById('task-title').value = t.title;
    document.getElementById('task-desc').value = t.description || '';
    document.getElementById('task-project').value = t.project_id;
    document.getElementById('task-status').value = t.status;
    document.getElementById('task-priority').value = t.priority;
    document.getElementById('task-modal-title').textContent = 'Редактировать задачу';
    openModal('task-modal');
}

async function deleteTask(id) {
    if (!confirm('Удалить задачу?')) return;
    
    try {
        await api(`/tasks/${id}`, { method: 'DELETE' });
        toast('Задача удалена', 'success');
        loadTasks();
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast(err.message, 'error');
    }
}

// Comments
async function showComments(taskId) {
    try {
        const data = await api(`/comments?task_id=${taskId}`);
        const comments = data.comments || [];
        
        document.getElementById('comment-task-id').value = taskId;
        
        const list = document.getElementById('comments-list');
        list.innerHTML = comments.length 
            ? comments.map(c => `
                <div class="comment">
                    <div class="comment-author">${esc(c.author?.username || 'Unknown')}</div>
                    <div class="comment-text">${esc(c.text)}</div>
                    <div class="comment-time">${fmtDate(c.created_at)}</div>
                </div>
            `).join('')
            : '<div class="no-comments">Нет комментариев</div>';
        
        openModal('comments-modal');
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast('Ошибка загрузки комментариев', 'error');
    }
}

async function saveComment(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('comment-task-id').value;
    const text = document.getElementById('comment-text').value;

    try {
        await api('/comments', {
            method: 'POST',
            body: JSON.stringify({ task_id: parseInt(taskId), text })
        });
        
        document.getElementById('comment-text').value = '';
        showComments(taskId);
        toast('Комментарий добавлен', 'success');
    } catch (err) {
        if (err.message !== 'AUTH_REQUIRED') toast(err.message, 'error');
    }
}

// Helpers
function updateSelects() {
    const selects = ['project-filter', 'task-project'];
    selects.forEach(id => {
        const sel = document.getElementById(id);
        if (!sel) return;
        
        const val = sel.value;
        let opts = id === 'project-filter' ? '<option value="">Все проекты</option>' : '';
        opts += projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
        
        sel.innerHTML = opts;
        if (val) sel.value = val;
    });
}

function getProjectName(id) {
    const p = projects.find(x => x.id === id);
    return p ? p.name : 'Unknown';
}

function statusLabel(s) {
    const map = { 'todo': 'К выполнению', 'in_progress': 'В работе', 'done': 'Выполнено', 'cancelled': 'Отменено' };
    return map[s] || s;
}

function priorityLabel(p) {
    const map = { 'low': 'Низкий', 'medium': 'Средний', 'high': 'Высокий', 'urgent': 'Срочный' };
    return map[p] || p;
}

function fmtDate(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function esc(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check auth
    if (localStorage.getItem('token')) {
        showDashboard();
    } else {
        showAuth();
    }

    // Auth forms
    document.getElementById('login').addEventListener('submit', (e) => {
        e.preventDefault();
        login();
    });

    document.getElementById('register').addEventListener('submit', (e) => {
        e.preventDefault();
        register();
    });

    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        showRegister();
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Modals
    document.getElementById('new-project-btn').addEventListener('click', () => {
        document.getElementById('project-form').reset();
        document.getElementById('project-id').value = '';
        document.getElementById('project-modal-title').textContent = 'Новый проект';
        openModal('project-modal');
    });

    document.getElementById('new-task-btn').addEventListener('click', () => {
        document.getElementById('task-form').reset();
        document.getElementById('task-id').value = '';
        document.getElementById('task-modal-title').textContent = 'Новая задача';
        openModal('task-modal');
    });

    document.getElementById('project-form').addEventListener('submit', saveProject);
    document.getElementById('task-form').addEventListener('submit', saveTask);
    document.getElementById('comment-form').addEventListener('submit', saveComment);

    // Filters
    document.getElementById('project-filter').addEventListener('change', loadTasks);
    document.getElementById('status-filter').addEventListener('change', loadTasks);

    // Close modals
    document.querySelectorAll('.close, .cancel-modal').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) modal.classList.add('hidden');
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.add('hidden');
        }
    });
});

// Global functions for onclick
window.editProject = editProject;
window.deleteProject = deleteProject;
window.editTask = editTask;
window.deleteTask = deleteTask;
window.showComments = showComments;
