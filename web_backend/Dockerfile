FROM python:3.10-slim

COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . ./app
WORKDIR ./app

ENTRYPOINT ["./run_gunicorn.sh"]
