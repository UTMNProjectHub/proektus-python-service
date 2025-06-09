import argparse
from pathlib import Path
import numpy as np

from app.features.tags.tags import TagsExtractor
from app.features.embeddings import SentenceEmbedder
from app.io.extractor import TextExtractor
from app.preprocessing.cleaner import TextCleaner

import os
from app.config.config import get_config
from app.io.s3_client import S3Client
from pathlib import Path
from typing import Optional, Union

from app.metadata_pipeline.orchestrator import PipelineOrchestrator
from app.downloader.downloader import ensure_spacy_model, ensure_all_nlp_dependencies

from pathlib import Path
from app.db.db_client import MetadataDBClient
from dotenv import load_dotenv

data = {
  "user_id": "user_id-для-связки-запрос-ответ",
  "project_id": 123,
  "object_keys": [
    "bucket1/path/to/file1.pdf",
    "bucket1/path/to/file2.docx"
  ]

}

class Pipeline:
    def __init__(self):
        load_dotenv()
        ensure_all_nlp_dependencies()
        self.db = MetadataDBClient()

        print("получение конфига")
        config = get_config()
        print("конфиг получен")

        print("создание экземпляра класса")
        self.s3_client = S3Client(config)
        print("экземпляр класса создан")

        self.orchestrator = PipelineOrchestrator(openai_key=config['OPENAI_TOKEN'])

    def run_pipeline(self, project_id, object_keys):
        downloaded_paths = []
        for i, object_key in enumerate(object_keys):
            # Скачиваем файл
            download_path = "downloaded_" + str(object_key)
            downloaded_paths.append(download_path)
            print(f"\nСкачивание файла {i+1} ...")
            object_key = self.s3_client.download_file_with_s3_key(object_key, download_path)
            print("Ключ скачанного объекта:", object_key)

        metadata = self.orchestrator.process_project(list_files_path=downloaded_paths, number_of_files=len(downloaded_paths))
        self.db.save_project_metadata(project_id, metadata)
        print('Обработка проекта завершена')
