FROM python:3.5-slim

RUN apt-get update && \
    apt-get install -y openssh-server

RUN apt-get clean

COPY src/ /data
RUN pip install -r /data/requirements.txt
WORKDIR /data
ENTRYPOINT ["python", "tunneler.py"]
