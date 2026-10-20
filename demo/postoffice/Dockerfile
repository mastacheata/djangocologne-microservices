FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DATA_DIR=/data
WORKDIR /app

COPY postoffice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ponybus.py .
COPY postoffice/ .

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000 --noreload"]
