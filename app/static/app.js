// API Configuration
const API_URL = window.location.origin;

// State
let currentUser = null;
let authToken = localStorage.getItem('token');
let projects = [];
let tasks = [];

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const projectsList = document.getElementById('projects-list');
const tasksList = document.getElementById('tasks-list');
const commentsList = document.getElementById('comments-list');
const toastContainer = document.getElementById('toast-container');

// Modals
const projectModal = document.getElementById('project-modal');
const taskModal = document.getElementById('task-modal');
const commentsModal = document.getElementById('comments-modal');

// API Helpers
async function apiRequest(endpoint, options = {}) {
    const url = `${API_URL}/api${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    if (authToken) {
        config.headers['Authorization'] = `Bearer ${authToken}`;
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || `HTTP ${response.status}`);
        }

        return data;
    } catch (error) {
        throw error;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Auth Functions
async function login(username, password) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(currentUser));

        showDashboard();
        showToast('Вход выполнен успешно!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function register(username, email, password) {
    try {
        await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });

        showToast('Регистрация успешна! Войдите в систему.', 'success');
        showLoginForm();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showAuthSection();
    showToast('Вы вышли из системы', 'info');
}

// UI Functions
function showAuthSection() {
    authSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
}

function showDashboard() {
    authSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('current-user').textContent = user.username;
    }

    loadProjects();
    loadTasks();
}

function showLoginForm() {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
}

function showRegisterForm() {
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
}

// Modal Functions
function openModal(modal) {
    modal.classList.remove('hidden');
}

function closeModal(modal) {
    modal.classList.add('hidden');
}

function closeAllModals() {
    [projectModal, taskModal, commentsModal].forEach(closeModal);
}

// Project Functions
async function loadProjects() {
    try {
        const data = await apiRequest('/projects');
        projects = data.projects || [];
        renderProjects();
        updateProjectSelects();
    } catch (error) {
        showToast('Ошибка загрузки проектов: ' + error.message, 'error');
    }
}

function renderProjects() {
    if (projects.length === 0) {
        projectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <p>У вас пока нет проектов</p>
            </div>
        `;
        return;
    }

    projectsList.innerHTML = projects.map(project => `
        <div class="card" data-project-id="${project.id}">
            <div class="card-header">
                <div class="card-title">${escapeHtml(project.name)}</div>
                <div class="card-actions">
                    <button class="btn btn-small btn-secondary" onclick="editProject(${project.id})">✏️</button>
                    <button class="btn btn-small btn-danger" onclick="deleteProject(${project.id})">🗑️</button>
                </div>
            </div>
            <div class="card-description">${escapeHtml(project.description || 'Нет описания')}</div>
            <div class="card-meta">
                <span>Создан: ${formatDate(project.created_at)}</span>
            </div>
        </div>
    `).join('');
}

async function saveProject(e) {
    e.preventDefault();
    
    const id = document.getElementById('project-id').value;
    const name = document.getElementById('project-name').value;
    const description = document.getElementById('project-desc').value;

    try {
        if (id) {
            await apiRequest(`/projects/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ name, description })
            });
            showToast('Проект обновлен', 'success');
        } else {
            await apiRequest('/projects', {
                method: 'POST',
                body: JSON.stringify({ name, description })
            });
            showToast('Проект создан', 'success');
        }

        closeModal(projectModal);
        loadProjects();
        document.getElementById('project-form').reset();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function editProject(id) {
    const project = projects.find(p => p.id === id);
    if (!project) return;

    document.getElementById('project-id').value = project.id;
    document.getElementById('project-name').value = project.name;
    document.getElementById('project-desc').value = project.description || '';
    document.getElementById('project-modal-title').textContent = 'Редактировать проект';
    
    openModal(projectModal);
}

async function deleteProject(id) {
    if (!confirm('Удалить проект? Все задачи будут удалены.')) return;

    try {
        await apiRequest(`/projects/${id}`, { method: 'DELETE' });
        showToast('Проект удален', 'success');
        loadProjects();
        loadTasks();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Task Functions
async function loadTasks() {
    try {
        const projectFilter = document.getElementById('project-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        let url = '/tasks?';
        if (projectFilter) url += `project_id=${projectFilter}&`;
        if (statusFilter) url += `status=${statusFilter}`;

        const data = await apiRequest(url);
        tasks = data.tasks || [];
        renderTasks();
    } catch (error) {
        showToast('Ошибка загрузки задач: ' + error.message, 'error');
    }
}

function renderTasks() {
    if (tasks.length === 0) {
        tasksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <p>Нет задач</p>
            </div>
        `;
        return;
    }

    tasksList.innerHTML = tasks.map(task => `
        <div class="card" data-task-id="${task.id}">
            <div class="card-header">
                <div class="card-title">${escapeHtml(task.title)}</div>
                <div>
                    <span class="badge status-${task.status}">${getStatusLabel(task.status)}</span>
                    <span class="badge priority-${task.priority}">${getPriorityLabel(task.priority)}</span>
                </div>
            </div>
            <div class="card-description">${escapeHtml(task.description || 'Нет описания')}</div>
            <div class="card-meta">
                <span>Проект: ${getProjectName(task.project_id)}</span>
                <div class="card-actions">
                    <button class="btn btn-small btn-secondary" onclick="editTask(${task.id})">✏️</button>
                    <button class="btn btn-small btn-secondary" onclick="showComments(${task.id})">💬</button>
                    <button class="btn btn-small btn-danger" onclick="deleteTask(${task.id})">🗑️</button>
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
            await apiRequest(`/tasks/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showToast('Задача обновлена', 'success');
        } else {
            await apiRequest('/tasks', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('Задача создана', 'success');
        }

        closeModal(taskModal);
        loadTasks();
        document.getElementById('task-form').reset();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function editTask(id) {
    const task = tasks.find(t => t.id === id);
    if (!task) return;

    document.getElementById('task-id').value = task.id;
    document.getElementById('task-title').value = task.title;
    document.getElementById('task-desc').value = task.description || '';
    document.getElementById('task-project').value = task.project_id;
    document.getElementById('task-status').value = task.status;
    document.getElementById('task-priority').value = task.priority;
    document.getElementById('task-modal-title').textContent = 'Редактировать задачу';
    
    openModal(taskModal);
}

async function deleteTask(id) {
    if (!confirm('Удалить задачу?')) return;

    try {
        await apiRequest(`/tasks/${id}`, { method: 'DELETE' });
        showToast('Задача удалена', 'success');
        loadTasks();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Comments Functions
async function showComments(taskId) {
    try {
        const data = await apiRequest(`/comments?task_id=${taskId}`);
        const comments = data.comments || [];
        
        document.getElementById('comment-task-id').value = taskId;
        
        if (comments.length === 0) {
            commentsList.innerHTML = '<div class="no-comments">Пока нет комментариев</div>';
        } else {
            commentsList.innerHTML = comments.map(comment => `
                <div class="comment">
                    <div class="comment-author">${escapeHtml(comment.author?.username || 'Unknown')}</div>
                    <div class="comment-text">${escapeHtml(comment.text)}</div>
                    <div class="comment-time">${formatDate(comment.created_at)}</div>
                </div>
            `).join('');
        }
        
        openModal(commentsModal);
    } catch (error) {
        showToast('Ошибка загрузки комментариев: ' + error.message, 'error');
    }
}

async function saveComment(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('comment-task-id').value;
    const text = document.getElementById('comment-text').value;

    try {
        await apiRequest('/comments', {
            method: 'POST',
            body: JSON.stringify({ task_id: parseInt(taskId), text })
        });

        document.getElementById('comment-text').value = '';
        showComments(taskId);
        showToast('Комментарий добавлен', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Helper Functions
function updateProjectSelects() {
    const selects = ['project-filter', 'task-project'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        const currentValue = select.value;
        
        let options = selectId === 'project-filter' 
            ? '<option value="">Все проекты</option>' 
            : '';
        
        options += projects.map(p => 
            `<option value="${p.id}">${escapeHtml(p.name)}</option>`
        ).join('');
        
        select.innerHTML = options;
        select.value = currentValue;
    });
}

function getProjectName(projectId) {
    const project = projects.find(p => p.id === projectId);
    return project ? project.name : 'Unknown';
}

function getStatusLabel(status) {
    const labels = {
        'todo': 'К выполнению',
        'in_progress': 'В работе',
        'done': 'Выполнено',
        'cancelled': 'Отменено'
    };
    return labels[status] || status;
}

function getPriorityLabel(priority) {
    const labels = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий',
        'urgent': 'Срочный'
    };
    return labels[priority] || priority;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', { 
        day: 'numeric', 
        month: 'short', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check auth status
    if (authToken) {
        showDashboard();
    } else {
        showAuthSection();
    }

    // Auth forms
    document.getElementById('login').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        login(username, password);
    });

    document.getElementById('register').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        register(username, email, password);
    });

    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterForm();
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        showLoginForm();
    });

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Project modal
    document.getElementById('new-project-btn').addEventListener('click', () => {
        document.getElementById('project-form').reset();
        document.getElementById('project-id').value = '';
        document.getElementById('project-modal-title').textContent = 'Новый проект';
        openModal(projectModal);
    });

    document.getElementById('project-form').addEventListener('submit', saveProject);

    // Task modal
    document.getElementById('new-task-btn').addEventListener('click', () => {
        document.getElementById('task-form').reset();
        document.getElementById('task-id').value = '';
        document.getElementById('task-modal-title').textContent = 'Новая задача';
        openModal(taskModal);
    });

    document.getElementById('task-form').addEventListener('submit', saveTask);

    // Comment form
    document.getElementById('comment-form').addEventListener('submit', saveComment);

    // Filters
    document.getElementById('project-filter').addEventListener('change', loadTasks);
    document.getElementById('status-filter').addEventListener('change', loadTasks);

    // Modal close buttons
    document.querySelectorAll('.close, .cancel-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            closeAllModals();
        });
    });

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeAllModals();
        }
    });
});

// Make functions available globally for onclick handlers
window.editProject = editProject;
window.deleteProject = deleteProject;
window.editTask = editTask;
window.deleteTask = deleteTask;
window.showComments = showComments;
