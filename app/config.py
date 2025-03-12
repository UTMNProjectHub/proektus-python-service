import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    return {
        "S3_ENDPOINT": os.getenv("S3_ENDPOINT"),
        "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
        "S3_ACCESS_KEY": os.getenv("S3_ACCESS_KEY"),
        "S3_SECRET_KEY": os.getenv("S3_SECRET_KEY"),
        "S3_SECURE": os.getenv("S3_SECURE").lower() in ['true', '1'],
        # todo: добавить другие параметры для подключения к PostgreSQL
    }
