from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from products import router as products_router
from auth import router as auth_router, get_current_user
from db.db_connection import get_connection
from random import sample

app = FastAPI()
app.include_router(products_router)
app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
db = get_connection()
products_collection = db["products"]


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: dict = Depends(get_current_user)):
    products = list(products_collection.find())

    recommended_products = []

    if user and "history" in user and user["history"]:
        last_history = [h for h in user["history"] if "category" in h][-6:]
        seen = set()
        last_categories = []
        for h in reversed(last_history):
            if h["category"] not in seen:
                seen.add(h["category"])
                last_categories.append(h["category"])
        recommended_products = list(
            products_collection.find({"category": {"$in": last_categories}}).limit(10)
        )
    else:
        all_products = list(products_collection.find())
        recommended_products = sample(all_products, min(10, len(all_products)))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "recommended_products": recommended_products,
        },
    )
