FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY pony/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ponybus.py .
COPY pony/pony.py .

CMD ["python", "pony.py"]
