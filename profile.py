from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db.db_connection import get_connection
from bson import ObjectId
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = get_connection()
products_collection = db["products"]
users_collection = db["users"]

@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Please log in"})

    user_data = users_collection.find_one({"_id": ObjectId(user["_id"])})
    if not user_data:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User not found"})

    liked_ids = user_data.get("liked_products", [])
    liked_products = []
    if liked_ids:
        liked_products = list(products_collection.find({"_id": {"$in": [ObjectId(pid) for pid in liked_ids]}}))

    history = user_data.get("history", [])
    categories = [h.get("category") for h in history if h.get("category")]
    top_categories = list({c for c in categories[-5:]}) if categories else []

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user_data,
            "liked_products": liked_products,
            "categories": top_categories
        }
    )
