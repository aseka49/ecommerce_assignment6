from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from products import router as products_router
from auth import router as auth_router, get_current_user
from profile import router as profile_router
from interaction import router as interactions_router
from admin_api import router as admin_router
from db.db_connection import get_connection
from random import sample


app = FastAPI()
app.include_router(products_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(interactions_router)
app.include_router(admin_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = get_connection()
products_collection = db["products"]
users_collection = db["users"]
interaction_collection = db["interaction"]

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: dict = Depends(get_current_user)):
    products = list(products_collection.find())
    recommended_products = []
    top_interactions = list(
        interaction_collection.aggregate([
            {"$match": {"type": {"$in": ["like", "view"]}}},
            {"$group": {"_id": "$product_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ])
    )

    top_ids = [item["_id"] for item in top_interactions]
    if top_ids:
        recommended_products = list(products_collection.find({"_id": {"$in": top_ids}}))
    if len(recommended_products) < 10 and user and "history" in user and user["history"]:
        last_categories = list({
            h["category"]
            for h in user["history"]
            if "category" in h
        })
        if last_categories:
            category_candidates = list(
                products_collection.find({"category": {"$in": last_categories}})
            )
            existing_ids = {p["_id"] for p in recommended_products}
            category_candidates = [p for p in category_candidates if p["_id"] not in existing_ids]
            needed = 10 - len(recommended_products)
            recommended_products.extend(sample(category_candidates, min(needed, len(category_candidates))))

    if len(recommended_products) < 10:
        existing_ids = {p["_id"] for p in recommended_products}
        remaining = [p for p in products if p["_id"] not in existing_ids]
        needed = 10 - len(recommended_products)
        recommended_products.extend(sample(remaining, min(needed, len(remaining))))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "recommended_products": recommended_products[:10],
        },
    )

