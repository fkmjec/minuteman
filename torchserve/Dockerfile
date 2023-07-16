FROM pytorch/torchserve:latest-gpu

ENV PATH "$PATH:/home/app/.local/bin"
USER root

USER model-server
# install the latest version of transformers 
RUN pip install transformers
