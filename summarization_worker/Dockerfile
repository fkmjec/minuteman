# build step to produce a leaner image
FROM python:3.10-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# final stage
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN addgroup --gid 1001 --system app && \
    adduser --shell /bin/false --disabled-password --uid 1001 --system --group app

# USER app

WORKDIR ./app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
ENV PATH "$PATH:/home/app/.local/bin"
RUN pip install --upgrade pip && pip install --no-cache /wheels/*
COPY . .
