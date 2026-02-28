from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = 'user'
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: Optional[str] = None

# Project schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: Optional[str] = None

# Task schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = 'todo'
    priority: Optional[str] = 'medium'
    project_id: int
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['todo', 'in_progress', 'done', 'cancelled']:
            raise ValueError('Status must be one of: todo, in_progress, done, cancelled')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'medium', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['todo', 'in_progress', 'done', 'cancelled']:
            raise ValueError('Status must be one of: todo, in_progress, done, cancelled')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and v not in ['low', 'medium', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    project_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Comment schemas
class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)
    task_id: int

class CommentUpdate(BaseModel):
    text: str = Field(..., min_length=1)

class CommentResponse(BaseModel):
    id: int
    text: str
    task_id: int
    author_id: int
    author: Optional[dict] = None
    created_at: Optional[str] = None

# Assignment schemas
class AssignmentCreate(BaseModel):
    task_id: int
    user_id: int

class AssignmentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    assigned_at: Optional[str] = None

# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse
