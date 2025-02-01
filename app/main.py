from fastapi import FastAPI, Depends
from routers import notes
from backend.db import engine, Base
from auth import get_current_username
from fastapi.templating import Jinja2Templates

app = FastAPI()


Base.metadata.create_all(bind=engine)

app.include_router(notes.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}