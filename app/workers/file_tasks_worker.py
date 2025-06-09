import os
import json
import logging

from redis import Redis
from python_laravel_queue import Queue as PlQueue

from app.metadata_pipeline.pipeline import Pipeline

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("Нужно задать REDIS_URL в окружении")
        return
    r = Redis.from_url(redis_url)

    queue_req = PlQueue(r, queue="file-tasks-requests", appname="", prefix="")

    queue_ans = PlQueue(r, queue="file-tasks-answers", appname="", prefix="queues:")

    pipeline = Pipeline()

    @queue_req.handler
    def handle_request(payload):
        """
        Обрабатывает задачу из file-tasks-requests:
         - запускает pipeline.run_pipeline
         - отправляет ответный Job в queues:file-tasks-requests
        """
        data = payload.get("data", {})
        user_id = data.get("user_id")
        project_id = data.get("project_id")
        object_keys = data.get("object_keys", [])
        print(data)

        logger.info(f"Принята задача для проекта {project_id}, user_id={user_id}")
        try:
            pipeline.run_pipeline(project_id, object_keys)
            status = "success"
            message = f"Проект {project_id} обработан успешно"
            logger.info(f"Проект {project_id} обработан")
        except Exception as e:
            status = "error"
            message = f"Ошибка обработки проекта {project_id}: {e}"
            logger.exception("Ошибка в run_pipeline")

        response_payload = {
            "userId":    user_id,
            "projectId": project_id,
            "status":     status,
            "message":    message,
        }
        queue_ans.push(
            "App\\Jobs\\HandleFileTaskAnswer",
            response_payload
        )
        logger.info(f"Отправлен ответ для проекта {project_id}")

    logger.info("Запуск subscriber file-tasks-requests…")
    queue_req.listen()


if __name__ == "__main__":
    main()
