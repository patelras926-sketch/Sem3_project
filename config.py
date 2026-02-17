# FarmIntel - Flask Configuration
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'farmintel-secret-key-change-in-production'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = 'farm_intel'
    MYSQL_CURSORCLASS = 'DictCursor'

    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    CROP_IMAGES_FOLDER = UPLOAD_FOLDER / 'crops'
    PRODUCT_IMAGES_FOLDER = UPLOAD_FOLDER / 'products'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    for folder in (UPLOAD_FOLDER, CROP_IMAGES_FOLDER, PRODUCT_IMAGES_FOLDER):
        folder.mkdir(parents=True, exist_ok=True)
