FROM python:3

LABEL maintainer="WardPearce <wardpearce@pm.me>"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./ /capycord

CMD [ "python", "./main.py" ]
