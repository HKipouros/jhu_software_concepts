FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
USER 1000
CMD ["python", "app.py"]