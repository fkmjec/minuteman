FROM pytorch/torchserve:latest-gpu

ENV PATH "$PATH:/home/app/.local/bin"
USER root
RUN apt update && apt install -y ffmpeg 

USER model-server
RUN pip install openai-whisper
