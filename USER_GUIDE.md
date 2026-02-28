# Руководство пользователя Task Manager API

## Содержание

1. [Введение](#введение)
2. [Установка и настройка](#установка-и-настройка)
3. [Быстрый старт](#быстрый-старт)
4. [API Reference](#api-reference)
5. [Примеры использования](#примеры-использования)
6. [Обработка ошибок](#обработка-ошибок)
7. [Развертывание](#развертывание)

---

## Введение

Task Manager API - это REST API для управления задачами и проектами. Система позволяет:

- Создавать и управлять проектами
- Создавать задачи с различными статусами и приоритетами
- Назначать исполнителей на задачи
- Оставлять комментарии
- Отслеживать прогресс через логи

### Схема базы данных

![ER Diagram](er_diagram.drawio)

**Таблицы:**
- `users` - пользователи системы
- `projects` - проекты (владелец - пользователь)
- `tasks` - задачи в проектах
- `task_assignments` - связь задач и исполнителей (многие-ко-многим)
- `comments` - комментарии к задачам

---

## Установка и настройка

### Требования

- Python 3.8+
- MySQL 5.7+ или 8.0+
- pip

### Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd taskmanager
```

### Шаг 2: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 3: Настройка базы данных

**Создание базы данных:**

```bash
mysql -u root -p
```

```sql
CREATE DATABASE taskmanager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'taskuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON taskmanager.* TO 'taskuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Импорт схемы:**

```bash
mysql -u taskuser -p taskmanager < database_schema.sql
```

### Шаг 4: Конфигурация окружения

```bash
cp .env.example .env
nano .env  # или используйте любой редактор
```

**Пример .env файла:**

```env
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

DB_USER=taskuser
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=taskmanager

LOG_FILE=app.log
LOG_LEVEL=INFO
```

> ⚠️ **Важно**: Никогда не коммитьте `.env` файл с реальными секретами в Git!

### Шаг 5: Инициализация базы данных (Flask-Migrate)

```bash
# Создание миграций
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## Быстрый старт

### Запуск сервера разработки

```bash
python run.py
```

Сервер запустится на `http://localhost:5000`

### Проверка работоспособности

```bash
curl http://localhost:5000/api/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "Task Manager API"
}
```

---

## API Reference

### Аутентификация

Все защищенные endpoints требуют JWT токен в заголовке:

```
Authorization: Bearer <your-jwt-token>
```

#### Регистрация

**POST** `/api/auth/register`

Создает нового пользователя.

**Тело запроса:**
```json
{
  "username": "string (3-50 символов)",
  "email": "valid@email.com",
  "password": "string (минимум 6 символов)",
  "role": "user" | "admin"  // опционально, по умолчанию "user"
}
```

**Ответ 201:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Ошибки:**
- `400` - Невалидные данные
- `409` - Username или email уже существует

#### Вход

**POST** `/api/auth/login`

**Тело запроса:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Ответ 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Ошибки:**
- `401` - Неверный username или password

### Пользователи

#### Список пользователей

**GET** `/api/users`

Требует: admin права

**Ответ 200:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### Получить пользователя

**GET** `/api/users/{id}`

Доступ: Свой профиль или admin

#### Обновить пользователя

**PUT** `/api/users/{id}`

**Тело запроса:**
```json
{
  "username": "new_username",  // опционально
  "email": "new@email.com",      // опционально
  "role": "admin"                // только для admin
}
```

#### Удалить пользователя

**DELETE** `/api/users/{id}`

Доступ: Свой профиль или admin

### Проекты

#### Список проектов

**GET** `/api/projects`

Возвращает проекты, где пользователь:
- Является владельцем
- Или назначен на задачи в проекте

**Ответ 200:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete redesign",
      "owner_id": 1,
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
```

#### Создать проект

**POST** `/api/projects`

**Тело запроса:**
```json
{
  "name": "string (обязательно, 1-100 символов)",
  "description": "string (опционально)"
}
```

#### Обновить проект

**PUT** `/api/projects/{id}`

Доступ: Владелец или admin

#### Удалить проект

**DELETE** `/api/projects/{id}`

Доступ: Владелец или admin

Удаляет проект и все связанные задачи (каскадное удаление)

### Задачи

#### Список задач

**GET** `/api/tasks`

**Query параметры:**
- `project_id` - фильтр по проекту
- `status` - `todo`, `in_progress`, `done`, `cancelled`
- `priority` - `low`, `medium`, `high`, `urgent`

**Пример:**
```bash
GET /api/tasks?project_id=1&status=todo&priority=high
```

#### Создать задачу

**POST** `/api/tasks`

**Тело запроса:**
```json
{
  "title": "string (обязательно, 1-200 символов)",
  "description": "string (опционально)",
  "status": "todo" | "in_progress" | "done" | "cancelled",
  "priority": "low" | "medium" | "high" | "urgent",
  "project_id": 1
}
```

#### Обновить задачу

**PUT** `/api/tasks/{id}`

Доступ: Владелец проекта, admin, или назначенный исполнитель

#### Удалить задачу

**DELETE** `/api/tasks/{id}`

Доступ: Владелец проекта или admin

#### Назначить исполнителя

**POST** `/api/tasks/{id}/assign`

**Тело запроса:**
```json
{
  "user_id": 2
}
```

**Ошибки:**
- `409` - Пользователь уже назначен

#### Убрать назначение

**DELETE** `/api/tasks/{id}/assign/{user_id}`

### Комментарии

#### Список комментариев

**GET** `/api/comments?task_id={id}`

**Ответ 200:**
```json
{
  "comments": [
    {
      "id": 1,
      "text": "Great progress!",
      "task_id": 1,
      "author_id": 2,
      "author": {
        "id": 2,
        "username": "jane_doe",
        ...
      },
      "created_at": "2024-01-15T11:00:00"
    }
  ]
}
```

#### Создать комментарий

**POST** `/api/comments`

**Тело запроса:**
```json
{
  "text": "string (обязательно)",
  "task_id": 1
}
```

#### Обновить комментарий

**PUT** `/api/comments/{id}`

Доступ: Только автор

#### Удалить комментарий

**DELETE** `/api/comments/{id}`

Доступ: Автор или admin

---

## Примеры использования

### Сценарий 1: Создание проекта и задач

```bash
# 1. Регистрация
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"manager","email":"manager@company.com","password":"pass123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

# 2. Вход
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"manager","password":"pass123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Создание проекта
PROJECT=$(curl -s -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Mobile App","description":"iOS/Android app development"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# 4. Создание задач
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"title\":\"Design UI mockups\",\"project_id\":$PROJECT,\"priority\":\"high\"}"

curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"title\":\"Setup backend API\",\"project_id\":$PROJECT,\"priority\":\"urgent\"}"
```

### Сценарий 2: Рабочий процесс с задачей

```bash
# Назначение исполнителя
curl -X POST http://localhost:5000/api/tasks/1/assign \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"user_id":2}'

# Обновление статуса
curl -X PUT http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status":"in_progress"}'

# Добавление комментария
curl -X POST http://localhost:5000/api/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text":"Started working on this","task_id":1}'

# Завершение задачи
curl -X PUT http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status":"done"}'
```

### Сценарий 3: Использование с Python

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Аутентификация
login_data = {
    "username": "manager",
    "password": "pass123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Получить все задачи с фильтром
params = {"status": "todo", "priority": "high"}
response = requests.get(f"{BASE_URL}/tasks", headers=headers, params=params)
tasks = response.json()["tasks"]

for task in tasks:
    print(f"Task: {task['title']} - {task['status']}")
```

### Сценарий 4: Фильтрация и отчеты

```bash
# Получить все срочные задачи
GET /api/tasks?priority=urgent

# Получить задачи в работе из проекта #1
GET /api/tasks?project_id=1&status=in_progress

# Получить все проекты и их задачи
GET /api/projects
# Для каждого проекта:
GET /api/tasks?project_id={project_id}
```

---

## Обработка ошибок

### Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | OK - Успешный запрос |
| 201 | Created - Ресурс создан |
| 400 | Bad Request - Невалидные данные |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Нет прав доступа |
| 404 | Not Found - Ресурс не найден |
| 409 | Conflict - Конфликт (например, дубликат) |
| 500 | Internal Server Error |

### Примеры ошибок

**Валидация (400):**
```json
{
  "error": "Validation failed",
  "details": [
    "username: ensure this value has at least 3 characters",
    "email: value is not a valid email address"
  ]
}
```

**Авторизация (401):**
```json
{
  "error": "Authorization token required"
}
```

**Доступ (403):**
```json
{
  "error": "Access denied - only owner or admin can update"
}
```

**Не найдено (404):**
```json
{
  "error": "Project not found"
}
```

**Конфликт (409):**
```json
{
  "error": "Username already exists"
}
```

---

## Развертывание

### PythonAnywhere

#### Шаг 1: Настройка

1. Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com)
2. Откройте Bash консоль
3. Клонируйте репозиторий:

```bash
git clone <your-repo-url> taskmanager
cd taskmanager
pip install -r requirements.txt
```

#### Шаг 2: База данных

1. В разделе **Databases** создайте MySQL базу
2. Запомните имя пользователя и пароль
3. Обновите `.env` файл

#### Шаг 3: Web App

1. В разделе **Web** нажмите **Add a new web app**
2. Выберите **Manual configuration** → **Python 3.9**
3. В поле **Source code**: `/home/yourusername/taskmanager`
4. В поле **Working directory**: `/home/yourusername/taskmanager`
5. В поле **WSGI configuration file** отредактируйте:

```python
import sys
path = '/home/yourusername/taskmanager'
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app
application = create_app('production')
```

6. В **Virtualenv** укажите путь к virtualenv (или оставьте пустым для глобального)

#### Шаг 4: Переменные окружения

В файле WSGI добавьте:

```python
import os
os.environ['SECRET_KEY'] = 'your-secret-key'
os.environ['JWT_SECRET_KEY'] = 'your-jwt-secret-key'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_PASSWORD'] = 'your-db-password'
os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_NAME'] = 'yourusername$taskmanager'
```

#### Шаг 5: Миграции

```bash
cd ~/taskmanager
flask db upgrade
```

#### Шаг 6: Перезагрузка

Нажмите **Reload** на странице Web.

### Другие хостинги

Для других хостингов (Heroku, DigitalOcean, AWS):

1. Установите переменные окружения
2. Настройте подключение к MySQL
3. Используйте `gunicorn`:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

---

## Логирование

Логи записываются в файл `app.log`:

```
2024-01-15 10:30:45 - app - INFO - ACTION: {
  'timestamp': '2024-01-15T10:30:45',
  'user_id': 1,
  'action': 'user_logged_in',
  'ip_address': '127.0.0.1',
  'status_code': 200
}
```

Для просмотра логов в реальном времени:

```bash
tail -f app.log
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный тест
pytest tests/test_api.py::TestAuth::test_login_success -v
```

### Структура тестов

- `test_auth.py` - Аутентификация
- `test_users.py` - Пользователи
- `test_projects.py` - Проекты
- `test_tasks.py` - Задачи
- `test_comments.py` - Комментарии
- `test_access_control.py` - Права доступа

---

## Поддержка

При возникновении проблем:

1. Проверьте логи: `cat app.log`
2. Проверьте подключение к базе данных
3. Убедитесь, что все переменные окружения установлены
4. Проверьте версии зависимостей: `pip list`

---

## Лицензия

MIT License - свободное использование для любых целей.
