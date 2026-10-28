FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt /srv/backend/requirements.txt
RUN pip install --no-cache-dir -r /srv/backend/requirements.txt
COPY backend/app /srv/backend/app
COPY data /srv/data
COPY models /srv/models
ENV PYTHONPATH=/srv/backend
EXPOSE 8000
CMD ["sh","-c","python -m app.seed 3000 50000 && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
