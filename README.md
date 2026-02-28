# Task Manager API

Полнофункциональное REST API для управления задачами, разработанное на Flask с использованием JWT-аутентификации, валидации Pydantic, логирования и тестов.

## Функции

- **Аутентификация и авторизация**: JWT токены, роли пользователей (admin/user)
- **Управление проектами**: Создание, чтение, обновление, удаление проектов
- **Управление задачами**: CRUD операции с задачами, статусы и приоритеты
- **Назначение исполнителей**: Назначение пользователей на задачи
- **Комментарии**: Добавление комментариев к задачам
- **Валидация данных**: Pydantic схемы для валидации входящих JSON
- **Логирование**: Запись всех действий пользователей и ошибок
- **Тестирование**: Полный набор тестов на pytest

## Технологический стек

- **Backend**: Flask 3.0, Flask-SQLAlchemy, Flask-JWT-Extended
- **Database**: MySQL (PyMySQL)
- **Validation**: Pydantic 2.x
- **Testing**: pytest, pytest-flask
- **Logging**: Встроенное логирование Python
- **Deployment**: PythonAnywhere-ready (WSGI)

## Структура проекта

```
taskmanager/
├── app/
│   ├── __init__.py          # Фабрика приложения
│   ├── config.py            # Конфигурация
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы валидации
│   ├── routes/              # API endpoints
│   │   ├── auth.py          # Аутентификация
│   │   ├── users.py         # Пользователи
│   │   ├── projects.py      # Проекты
│   │   ├── tasks.py         # Задачи
│   │   └── comments.py      # Комментарии
│   └── utils/               # Утилиты
│       ├── decorators.py    # JWT декораторы
│       └── logger.py        # Логирование
├── tests/                   # Тесты
│   ├── conftest.py          # Фикстуры pytest
│   └── test_api.py          # API тесты
├── er_diagram.drawio        # ER-диаграмма
├── database_schema.sql      # SQL схема
├── requirements.txt         # Зависимости
├── run.py                   # Точка входа (dev)
├── wsgi.py                  # WSGI для PythonAnywhere
└── .env.example             # Пример конфигурации
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте MySQL базу данных:

```sql
CREATE DATABASE taskmanager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Или используйте SQL дамп:

```bash
mysql -u root -p taskmanager < database_schema.sql
```

### 3. Конфигурация окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=taskmanager
```

### 4. Запуск приложения

```bash
python run.py
```

API будет доступен по адресу: `http://localhost:5000`

## API Endpoints

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/auth/register` | Регистрация нового пользователя |
| POST | `/api/auth/login` | Вход и получение JWT токена |

### Пользователи

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/users` | Список всех пользователей (admin) |
| GET | `/api/users/<id>` | Получить пользователя по ID |
| PUT | `/api/users/<id>` | Обновить пользователя |
| DELETE | `/api/users/<id>` | Удалить пользователя |

### Проекты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/projects` | Список проектов пользователя |
| GET | `/api/projects/<id>` | Получить проект по ID |
| POST | `/api/projects` | Создать проект |
| PUT | `/api/projects/<id>` | Обновить проект |
| DELETE | `/api/projects/<id>` | Удалить проект |

### Задачи

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/tasks` | Список задач (с фильтрами) |
| GET | `/api/tasks/<id>` | Получить задачу по ID |
| POST | `/api/tasks` | Создать задачу |
| PUT | `/api/tasks/<id>` | Обновить задачу |
| DELETE | `/api/tasks/<id>` | Удалить задачу |
| POST | `/api/tasks/<id>/assign` | Назначить исполнителя |
| DELETE | `/api/tasks/<id>/assign/<user_id>` | Убрать назначение |

### Комментарии

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/comments?task_id=<id>` | Список комментариев задачи |
| GET | `/api/comments/<id>` | Получить комментарий |
| POST | `/api/comments` | Добавить комментарий |
| PUT | `/api/comments/<id>` | Обновить комментарий |
| DELETE | `/api/comments/<id>` | Удалить комментарий |

### Служебные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/health` | Проверка работоспособности |

## Примеры использования

### 1. Регистрация пользователя

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

**Ответ:**
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

### 2. Вход в систему

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

**Ответ:**
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

### 3. Создание проекта

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Website Redesign",
    "description": "Complete redesign of company website"
  }'
```

**Ответ:**
```json
{
  "message": "Project created successfully",
  "project": {
    "id": 1,
    "name": "Website Redesign",
    "description": "Complete redesign of company website",
    "owner_id": 1,
    "created_at": "2024-01-15T10:35:00"
  }
}
```

### 4. Создание задачи

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Design homepage mockup",
    "description": "Create initial design mockup for homepage",
    "status": "todo",
    "priority": "high",
    "project_id": 1
  }'
```

**Ответ:**
```json
{
  "message": "Task created successfully",
  "task": {
    "id": 1,
    "title": "Design homepage mockup",
    "description": "Create initial design mockup for homepage",
    "status": "todo",
    "priority": "high",
    "project_id": 1,
    "created_at": "2024-01-15T10:40:00",
    "updated_at": "2024-01-15T10:40:00",
    "assignees": []
  }
}
```

### 5. Фильтрация задач

**Запрос:**
```bash
curl "http://localhost:5000/api/tasks?status=todo&priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ответ:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Design homepage mockup",
      "status": "todo",
      "priority": "high",
      ...
    }
  ]
}
```

### 6. Назначение исполнителя

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/tasks/1/assign \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": 2
  }'
```

### 7. Добавление комментария

**Запрос:**
```bash
curl -X POST http://localhost:5000/api/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Great progress! Keep it up.",
    "task_id": 1
  }'
```

## Валидация данных

Приложение использует Pydantic для валидации входящих данных. При невалидных данных возвращается ошибка 400 с подробным описанием:

**Пример невалидного запроса:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ab",
    "email": "invalid-email",
    "password": "123"
  }'
```

**Ответ:**
```json
{
  "error": "Validation failed",
  "details": [
    "username: ensure this value has at least 3 characters",
    "email: value is not a valid email address",
    "password: ensure this value has at least 6 characters"
  ]
}
```

## Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -v

# Запуск с покрытием кода
pytest --cov=app --cov-report=html
```

## Логирование

Все действия пользователей и ошибки записываются в файл `app.log`:

```
2024-01-15 10:30:45 - app - INFO - ACTION: {'timestamp': '2024-01-15T10:30:45', 'user_id': 1, 'action': 'user_registered', ...}
2024-01-15 10:35:12 - app - ERROR - ERROR: {'timestamp': '2024-01-15T10:35:12', 'error': 'Login failed', ...}
```

## Развертывание на PythonAnywhere

1. Загрузите код на PythonAnywhere через Git или файловый менеджер
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте WSGI файл (уже готов в `wsgi.py`)
4. Обновите путь в `wsgi.py` на ваш путь PythonAnywhere
5. Настройте MySQL базу данных в разделе Databases
6. Примените миграции: `flask db upgrade`

## Git Версии

Проект содержит следующие версии:

- **v1.0** (fbc03eb): Initial commit - базовая структура, аутентификация, CRUD операции

## Лицензия

MIT License
