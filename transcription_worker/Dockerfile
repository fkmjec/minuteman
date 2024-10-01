# Build stage
FROM nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04 as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN apt-get update && apt-get install -y python3-pip python-is-python3 && \
    pip3 install --upgrade pip && \
    pip3 wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04

WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
ENV PATH="$PATH:/home/app/.local/bin"
RUN apt-get update && apt-get install -y python3-pip python-is-python3 && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache /wheels/*
COPY . .

ENTRYPOINT ["python", "transcription_worker.py"]
