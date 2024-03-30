# build step to produce a leaner image
FROM python:3.10-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM node:18-alpine as npmbuilder
COPY static .
RUN npm install
RUN npx webpack

# final stage
FROM python:3.10-slim

RUN addgroup --gid 1001 --system app && \
    adduser --shell /bin/false --disabled-password --uid 1001 --system --group app

# USER app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR ./app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
ENV PATH "$PATH:/home/app/.local/bin"
RUN pip install --upgrade pip && pip install --no-cache /wheels/*
COPY --from=npmbuilder /dist/main.js ./static/dist/main.js
COPY --from=npmbuilder /dist/VoiceRecorder.js ./static/dist/VoiceRecorder.js
COPY . .
