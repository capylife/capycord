import os

from dotenv import load_dotenv

load_dotenv()


CHECK_DELAY = int(os.getenv("CHECK_DELAY", 120))
CAPY_LIFE_LINK = os.getenv("CAPY_LIFE_LINK", "https://capy.life")
CAPY_API_LINK = os.getenv("CAPY_API_LINK", "https://capy.life/api/")

MONGO_HOST = os.getenv("MONGO_IP", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB = os.getenv("MONGO_DB", "capycord")
