FROM python:3.9-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "python manage.py migrate && python manage.py loaddata db_dump.json && gunicorn stripe_project.wsgi"]  
# :application --bind 0.0.0.0:8000"