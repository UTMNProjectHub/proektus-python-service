import os


def get_s3_credentials():
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    endpoint = os.getenv("S3_ENDPOINT")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    print(access_key)
    print(secret_key)
    print(endpoint)
    print(bucket_name)


    if not all([access_key, secret_key, endpoint, bucket_name]):
        raise ValueError("Не заданы все переменные окружения для подключения к S3")

    return {
        "endpoint": endpoint,
        "bucket_name": bucket_name,
        "access_key": access_key,
        "secret_key": secret_key,
        "secure": os.getenv("S3_SECURE", "False").lower() in ['true', '1']
    }
