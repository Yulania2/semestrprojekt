import os
import shutil
from fastapi import FastAPI, File, Form, Request, Depends, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pytest import Session
from auth import get_current_user_id 

from db import Post, User, get_db




app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)




database = {
    "users": {
        "admin": {
            "username": "admin",
            "password": hash_password("admin123"),
            "is_admin": True,
            "favorites": []
        }
    },
    "posts": []  # Список для збереження постів
}




# Home Page

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    if username in database["users"]:
        raise HTTPException(status_code=400, detail="Username already exists")

    database["users"][username] = {
        "username": username,
        "password": hash_password(password),
        "is_admin": False,
        "favorites": []
    }
    return RedirectResponse("/login", status_code=303)




# Login
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = database["users"].get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user.get("is_admin"):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse(f"/user/{form_data.username}", status_code=303)

# Сторінка адміністратора - створити допис
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})




# Home Page
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/admin/create_post")
async def create_post(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),  # Отримуємо ID користувача
):
    # Переконайтися, що директорія існує
    os.makedirs("static/images", exist_ok=True)

    # Збереження зображення
    image_path = f"static/images/{image.filename}"
    with open(image_path, "wb") as file:
        shutil.copyfileobj(image.file, file)

    # Створення поста в базі даних
    post = Post(
        title=title,
        description=description,
        image=image_path,
        user_id=user_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {"message": "Post created successfully"}



# Сторінка користувача - перегляд дописів і вибраного
@app.get("/user/{username}", response_class=HTMLResponse)
async def user_page(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = db.query(Post).filter(Post.user_id == user.id).all()
    return templates.TemplateResponse("user.html", {
        "request": request,
        "username": username,
        "posts": posts,
        "favorites": []  
    })

@app.post("/user/{username}/add_favorite")
async def add_to_favorites(username: str, post_title: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post = db.query(Post).filter(Post.title == post_title).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # реалізація фактичного зв’язку з базою даних
    return RedirectResponse(f"/user/{username}", status_code=303)

@app.get("/user/{username}/favorites", response_class=HTMLResponse)
async def user_favorites_page(request: Request, username: str):
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "username": username,
        "favorites": [] 
    })   