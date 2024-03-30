# build step to produce a leaner image
FROM tensorflow/tensorflow:devel-gpu as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# final stage, tensorflow for correct GPU support (probably can be done smarter)
FROM tensorflow/tensorflow:devel-gpu
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
