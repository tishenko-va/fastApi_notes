from fastapi import FastAPI, Depends, Request
from routers import notes
from backend.db import engine, Base
from auth import get_current_username
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()


Base.metadata.create_all(bind=engine)

app.include_router(notes.router)

templates = Jinja2Templates(directory="templates")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})