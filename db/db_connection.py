from pymongo import MongoClient


def get_connection():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["ecommerce"]
    return db


