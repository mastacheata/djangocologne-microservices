FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install --no-cache-dir pika==1.3.2

COPY shared/ponybus.py .
COPY logbook/logbook.py .

CMD ["python", "logbook.py"]
