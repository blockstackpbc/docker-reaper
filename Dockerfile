# default env set to quay
ENV TYPE="quay"
FROM python:3
USER root

RUN pip3 install -U pip && \
  pip install -U requests

COPY quay.py .
COPY dockerhub.py .
ENTRYPOINT /usr/bin/python3 /${TYPE}.py
