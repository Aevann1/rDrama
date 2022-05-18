FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt -y upgrade && apt install -y supervisor python3-pip libenchant1c2a ffmpeg

COPY supervisord.conf /etc/supervisord.conf

COPY requirements.txt /etc/requirements.txt

RUN pip3 install -r /etc/requirements.txt

RUN mkdir /images && mkdir /songs && mkdir /videos

EXPOSE 80/tcp

CMD [ "/usr/bin/supervisord", "-c", "/etc/supervisord.conf" ]
