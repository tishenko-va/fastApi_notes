from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db_depends import get_db
from models.models import Note, User
from schemas import NoteCreate, NoteUpdate
from slugify import slugify
from fastapi import Path, status, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext
from fastapi import Form
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import (create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES,
                  oauth2_scheme, SECRET_KEY, ALGORITHM, get_current_username)

from sqlalchemy import select

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = pwd_context.hash(password)
    db_user = User(username=username, password=hashed_password)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return RedirectResponse(url="/all_notes", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if user is None or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_class=HTMLResponse)
async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if user is None or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    return RedirectResponse(url="/all_notes", status_code=303)


@router.get('/all_notes', response_class=HTMLResponse)
async def all_notes(
        request: Request,
        db: Session = Depends(get_db)
):
    stmt = select(Note)
    result = db.execute(stmt)
    notes = result.scalars().all()
    return templates.TemplateResponse("note.html", {"request": request, "notes": notes})


@router.post("/create", response_class=HTMLResponse)
async def create_note(
        request: Request,
        title: str = Form(...),
        content: str = Form(...),
        db: Session = Depends(get_db)

):

    new_note = Note(
        title=title,
        content=content,
        slug=slugify(title)
    )

    try:
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return RedirectResponse(url="/all_notes", status_code=303)


@router.get('/update/{note_id}', response_class=HTMLResponse)
async def get_update_note_page(note_id: int, request: Request, db: Session = Depends(get_db)):
    query = select(Note).where(Note.id == note_id)
    note = db.scalar(query)

    if note:
        return templates.TemplateResponse("update.html", {"request": request, "note": note})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

@router.post('/update/{note_id}', response_class=HTMLResponse)
async def update_note(
    note_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    query = select(Note).where(Note.id == note_id)
    note = db.scalar(query)

    if note:
        note.title = title
        note.content = content
        try:
            db.commit()
            return RedirectResponse(url="/all_notes", status_code=303)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

@router.post('/delete/{note_id}', response_class=HTMLResponse)
async def delete_note(
        note_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    query = select(Note).where(Note.id == note_id)
    note = db.scalar(query)

    if note:
        try:
            db.delete(note)
            db.commit()
            return RedirectResponse(url="/all_notes", status_code=303)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
