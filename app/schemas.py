from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    id: int
    username: str
    password: str


class NoteBase(BaseModel):
    title: str
    content: str

class NoteCreate(NoteBase):
    id: int
    title: str
    content: str

class NoteUpdate(NoteBase):
    title: str
    content: str


class Notes(NoteBase):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

