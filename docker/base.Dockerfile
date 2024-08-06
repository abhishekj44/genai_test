FROM python:3.10.11 as base

ARG http_proxy \
    https_proxy \
    no_proxy

ENV http_proxy ${http_proxy}
ENV https_proxy ${https_proxy}
ENV no_proxy ${no_proxy}

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.base.txt /app

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install pysqlite3==0.5.2
RUN pip install pyjwt==2.8.0
RUN pip install httpx_oauth==0.14.1
RUN pip install --no-cache-dir -r requirements.base.txt
RUN pip install pysqlite3-binary
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
