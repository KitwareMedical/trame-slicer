FROM ubuntu:24.04

WORKDIR /app

# Avoid buffering the server URL
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y libgl1-mesa-dri mesa-utils libegl1 libgles2 libosmesa6-dev python3-pip python3.12-venv

# Prevent apt from prompting us about various decisions
ENV DEBIAN_FRONTEND=noninteractive

# Allow driver to do rendering
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV NVIDIA_VISIBLE_DEVICES=all

RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install trame-slicer[standalone]

COPY app.py /app/app.py
COPY docker_run.sh /app/docker_run.sh
RUN chmod +x /app/docker_run.sh

ENTRYPOINT ["/bin/bash", "/app/docker_run.sh"]
