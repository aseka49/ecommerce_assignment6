from fastapi import APIRouter, Depends, HTTPException, Form
from bson import ObjectId
from db.db_connection import get_connection
from auth import get_current_user, required_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
db = get_connection()
products_collection = db["products"]


@router.post("/products/add")
def add_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    user: dict = Depends(get_current_user),
    image_url: str = Form(...)
):
    required_admin(user)

    product = {
        "name": name,
        "description": description,
        "category": category,
        "price": price,
        "created_by": str(user["_id"]),
        "image": image_url
    }
    result = products_collection.insert_one(product)
    return {"message": "Product added", "id": str(result.inserted_id)}


@router.put("/products/{product_id}")
def update_product(
    product_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    category: str | None = Form(None),
    price: float | None = Form(None),
    user: dict = Depends(get_current_user),
    image_url: str | None = Form(None)
):
    required_admin(user)

    update_fields = {}
    if name:
        update_fields["name"] = name
    if description:
        update_fields["description"] = description
    if category:
        update_fields["category"] = category
    if price:
        update_fields["price"] = price
    if image_url:
        update_fields["image"] = image_url

    if not update_fields:
        raise HTTPException(status_code=400, detail="No data for update")

    result = products_collection.update_one(
        {"_id": ObjectId(product_id)}, {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product was not found")

    return {"message": "Product updated"}


@router.delete("/products/{product_id}")
def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    required_admin(user)

    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product was not found")

    return {"message": "Product deleted"}
