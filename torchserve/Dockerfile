FROM pytorch/torchserve:latest-gpu

ENV PATH "$PATH:/home/app/.local/bin"
USER root
RUN apt update && apt install -y ffmpeg git

USER model-server
# install the latest version of transformers, accelerate and 
RUN pip install bitsandbytes>=0.39.0 && pip install git+https://github.com/huggingface/accelerate.git && pip install git+https://github.com/huggingface/transformers.git
