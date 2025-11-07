from fastapi import APIRouter, Request, HTTPException, status, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
import bcrypt
from db.db_connection import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = get_connection()
users_collection = db["users"]

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# HTML страницы
@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# API регистрация
@router.post("/register")
def register_user(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user_data = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "history": [],
        "liked_products": [],
        "registration_date": datetime.utcnow(),
        "role": "user"
    }
    users_collection.insert_one(user_data)
    return RedirectResponse(url="/login", status_code=303)


# API вход
@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    db_user = users_collection.find_one({"email": email})
    if not db_user or not bcrypt.checkpw(password.encode(), db_user["password"]):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    token = jwt.encode({"user_id": str(db_user["_id"])}, SECRET_KEY, algorithm=ALGORITHM)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    from bson import ObjectId
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def required_admin(user: dict):
    if user.get("role") != "admin":
        return RedirectResponse(url='/', status_code=303)
