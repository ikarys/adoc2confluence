FROM docker.io/asciidoctor/docker-asciidoctor

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools atlassian-python-api beautifulsoup4

COPY default.css default.css
COPY adoc2confluence.py adoc2confluence.py
