import uuid
import hashlib
from minio import Minio
from minio.error import S3Error


class S3Client:
    """
    A class to work with S3-compatible storage.

    This class provides methods to:
      - Upload files with their original names and a unique file_id.
      - Allow different users to upload files with the same name.
      - Warn if a user uploads a duplicate file (based on file hash).
      - List files, download files, and get file metadata.
      - Link files to database records using a unique file_id.
    """

    def __init__(self, config):
        """
        Initialize the S3Client with configuration settings.

        Args:
            config (dict): A dictionary with keys:
                - S3_BUCKET_NAME: The S3 bucket name.
                - S3_ENDPOINT: The S3 endpoint URL.
                - S3_ACCESS_KEY: The access key.
                - S3_SECRET_KEY: The secret key.
                - S3_SECURE: Boolean for secure connection.

        This method also creates the bucket if it does not exist.
        """
        self.bucket_name = config["S3_BUCKET_NAME"]
        self.client = Minio(
            config["S3_ENDPOINT"],
            access_key=config["S3_ACCESS_KEY"],
            secret_key=config["S3_SECRET_KEY"],
            secure=config["S3_SECURE"]
        )
        # Создаем бакет, если его нет
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def compute_file_hash(self, file_path, algorithm='sha256', chunk_size=4096):
        """
        Compute the hash of a file.

        Args:
            file_path (str): The path to the file.
            algorithm (str, optional): The hash algorithm to use (default is 'sha256').
            chunk_size (int, optional): The chunk size for reading the file.

        Returns:
            str: The hexadecimal hash of the file.
        """
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def check_duplicate(self, user_id, file_hash):
        """
        Check if a file with the same hash exists for the given user.

        Args:
            user_id (str): The user's ID.
            file_hash (str): The hash of the file.

        Returns:
            list: A list of object keys that match the file hash.
        """
        duplicates = []
        prefix = f"{user_id}/"
        objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
        for obj in objects:
            try:
                stat = self.client.stat_object(self.bucket_name, obj.object_name)
                meta_hash = stat.metadata.get("file_hash")
                if meta_hash == file_hash:
                    duplicates.append(obj.object_name)
            except S3Error as e:
                print(f"Ошибка при получении метаданных объекта {obj.object_name}: {e}")
        return duplicates

    def upload_file(self, file_path, original_name, user_id, project_id=None):
        """
        Upload a file to S3 with its metadata.

        Args:
            file_path (str): The path to the file.
            original_name (str): The original file name.
            user_id (str): The user's ID.
            project_id (str, optional): The project ID.

        Returns:
            dict or None: A dictionary with file_id, object_key, and file_hash if successful; None otherwise.
        """
        # Преобразование оригинального имени в ASCII-safe вариант
        safe_original_name = original_name.encode("ascii", "ignore").decode("ascii")
        file_hash = self.compute_file_hash(file_path)
        duplicates = self.check_duplicate(user_id, file_hash)
        if duplicates:
            print(f"Предупреждение: найден дубликат файла для пользователя {user_id}: {duplicates}")
            # todo: Здесь можно остановить загрузку или продолжить загрузку уведомив пользователя

        file_id = str(uuid.uuid4())
        # Используем безопасное имя в ключе объекта
        object_key = f"{user_id}/{file_id}_{safe_original_name}"

        metadata = {
            "original_name": safe_original_name,  # ASCII-safe вариант
            "file_id": file_id,
            "file_hash": file_hash,
        }
        if project_id:
            metadata["project_id"] = str(project_id)

        try:
            self.client.fput_object(self.bucket_name, object_key, file_path, metadata=metadata)
            print(f"Файл успешно загружен с ключом: {object_key}")
            return {"file_id": file_id, "object_key": object_key, "file_hash": file_hash}
        except S3Error as e:
            print(f"Ошибка загрузки файла: {e}")
            return None

    def download_file(self, user_id, file_id, destination_path):
        """
        Download a file from S3 using its file_id.

        The method searches for the object using the prefix "user_id/file_id_".

        Args:
            user_id (str): The user's ID.
            file_id (str): The unique file ID.
            destination_path (str): The local path to save the downloaded file.

        Returns:
            str or None: The object key of the downloaded file if successful; None otherwise.
        """
        prefix = f"{user_id}/{file_id}_"
        objects = list(self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True))
        if not objects:
            print(f"Файл с file_id {file_id} для пользователя {user_id} не найден")
            return None
        if len(objects) > 1:
            print(f"Найдено несколько объектов для file_id {file_id}, ожидается один")
        object_key = objects[0].object_name
        try:
            self.client.fget_object(self.bucket_name, object_key, destination_path)
            print(f"Файл {object_key} скачан в {destination_path}")
            return object_key
        except S3Error as e:
            print(f"Ошибка скачивания файла: {e}")
            return None

    def get_file_metadata(self, user_id, file_id):
        """
        Retrieve the metadata of a file from S3 using its file_id.

        Args:
            user_id (str): The user's ID.
            file_id (str): The unique file ID.

        Returns:
            dict or None: The file's metadata if found; None otherwise.
        """
        prefix = f"{user_id}/{file_id}_"
        objects = list(self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True))
        if not objects:
            print(f"Объект с file_id {file_id} для пользователя {user_id} не найден")
            return None
        object_key = objects[0].object_name
        try:
            stat = self.client.stat_object(self.bucket_name, object_key)
            return stat.metadata
        except S3Error as e:
            print(f"Ошибка получения метаданных: {e}")
            return None

    def list_files(self, user_id, prefix=""):
        """
        List all files for a given user.

        Args:
            user_id (str): The user's ID.
            prefix (str, optional): Additional prefix to filter files.

        Returns:
            list: A list of object keys for the user's files.
        """
        full_prefix = f"{user_id}/{prefix}"
        objects = list(self.client.list_objects(self.bucket_name, prefix=full_prefix, recursive=True))
        return [obj.object_name for obj in objects]

    def download_file_with_s3_key(self, s3_key, destination_path):
        objects = list(self.client.list_objects(self.bucket_name, prefix=s3_key, recursive=True))
        if not objects:
            print(f"Файл {s3_key} не найден")
            return None
        if len(objects) > 1:
            print(f"Найдено несколько объектов для s3_key= {s3_key}, ожидается один")
        try:
            self.client.fget_object(self.bucket_name, s3_key, destination_path)
            print(f"Файл {s3_key} скачан в {destination_path}")
            return s3_key
        except S3Error as e:
            print(f"Ошибка скачивания файла: {e}")
            return None