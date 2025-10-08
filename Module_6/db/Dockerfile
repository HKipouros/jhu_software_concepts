# Dockerfile for data_loader service
FROM python:3.11-slim

WORKDIR /app

COPY load_data.py .
COPY applicant_data.json .

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install psycopg
RUN pip install dotenv

# Command to run the data loading script
CMD ["python", "load_data.py"]