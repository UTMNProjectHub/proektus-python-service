FROM python:3.10.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /myservice

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .


ENV PYTHONPATH=/myservice

CMD ["python", "app/workers/file_tasks_worker.py"]
