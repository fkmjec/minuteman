# FROM pytorch/torchserve:latest-gpu
FROM pytorch/torchserve:0.11.0-cpu

ENV PATH "$PATH:/home/app/.local/bin"
USER root

USER model-server
# install the latest version of transformers
RUN pip install transformers
