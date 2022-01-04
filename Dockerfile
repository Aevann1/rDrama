FROM ubuntu:20.04

RUN apt update && apt install -y python3.8 python3-pip

COPY requirements.txt /service/requirements.txt

WORKDIR /service

RUN pip3 install -r requirements.txt

EXPOSE 80/tcp

CMD waitress-serve --port=80 files.__main__:app