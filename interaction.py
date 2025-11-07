from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from db.db_connection import get_connection
from auth import get_current_user

router = APIRouter()
db = get_connection()
interactions_collection = db["interaction"]
products_collection = db["products"]
users_collection = db["users"]


@router.post("/interact/{product_id}/{action}")
async def record_interaction(product_id: str, action: str, user=Depends(get_current_user)):
    if action not in ["view", "like", "add_to_cart"]:
        raise HTTPException(status_code=400, detail="Invalid action type")

    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    interaction = {
        "user_id": ObjectId(user["_id"]),
        "product_id": ObjectId(product_id),
        "type": action,
        "timestamp": datetime.utcnow()
    }
    interactions_collection.insert_one(interaction)

    if action == "like":
        users_collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$addToSet": {"liked_products": str(product_id)}}
        )

    return {"status": "ok", "action": action}


@router.post("/like/{product_id}")
def like_product(product_id: str, user: dict = Depends(get_current_user)):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    existing = interactions_collection.find_one({
        "user_id": ObjectId(user["_id"]),
        "product_id": ObjectId(product_id),
        "type": "like"
    })

    if existing:
        interactions_collection.delete_one({"_id": existing["_id"]})
        liked = False
        users_collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$pull": {"liked_products": str(product_id)}}
        )
    else:
        interactions_collection.insert_one({
            "user_id": ObjectId(user["_id"]),
            "product_id": ObjectId(product_id),
            "type": "like",
            "timestamp": datetime.utcnow()
        })
        liked = True
        users_collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$addToSet": {"liked_products": str(product_id)}}
        )

    return {"liked": liked}


@router.get("/interactions")
async def get_user_interactions(user=Depends(get_current_user)):
    interactions = list(interactions_collection.find({"user_id": ObjectId(user["_id"])}))
    return {"interactions": interactions}
