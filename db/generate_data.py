from db_connection import get_connection

db = get_connection()


def user_collection():
    return db.users.find()


def products_collection():
    return db.products.find()


collection = db["products"]


class Product:
    def __init__(self, name: str, description: str, category: str, price: float, image_url: str):
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.image_url = image_url

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "image_url": self.image_url
        }



