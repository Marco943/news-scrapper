import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo = MongoClient(os.environ.get("DB_ECONODATA"))
