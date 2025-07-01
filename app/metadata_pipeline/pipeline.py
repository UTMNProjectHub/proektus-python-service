from pathlib import Path
import os
from app.config.config import get_config
from app.io.s3_client import S3Client
from typing import Optional, Union

from app.metadata_pipeline.orchestrator import PipelineOrchestrator
from app.downloader.downloader import ensure_spacy_model, ensure_all_nlp_dependencies

from app.db.db_client import MetadataDBClient
from dotenv import load_dotenv


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
            download_path = "downloaded_" + str(object_key)
            downloaded_paths.append(download_path)
            object_key = self.s3_client.download_file_with_s3_key(object_key, download_path)

        metadata = self.orchestrator.process_project(list_files_path=downloaded_paths, number_of_files=len(downloaded_paths))
        self.db.save_project_metadata(project_id, metadata)
        print('Обработка проекта завершена')
