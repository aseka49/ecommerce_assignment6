from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db.db_connection import get_connection
from bson import ObjectId
from auth import get_current_user
from datetime import datetime


router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = get_connection()
products_collection = db["products"]
users_collection = db["users"]
interaction_collection = db["interaction"]

@router.get("/products", response_class=HTMLResponse)
def get_products(
    request: Request,
    category: str | None = Query(default=None),
    name: str | None = Query(default=None),
    user: dict = Depends(get_current_user)
):
    query = {}

    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    products = list(products_collection.find(query))
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
            "user": user
        }
    )



@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: str, user: dict = Depends(get_current_user)):
    product = products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    interaction_collection.update_one(
        {"user_id": ObjectId(user["_id"]), "product_id": ObjectId(product_id)},
        {
            "$set": {
                "type": "view",
                "timestamp": datetime.utcnow()
            }
        },
        upsert=True
    )

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$push": {"history": {
            "product_id": product_id,
            "action": "view",
            "category": product["category"],
            "timestamp": datetime.utcnow()
        }}}
    )

    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product, "user": user}
    )
