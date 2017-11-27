FROM alpine:latest

RUN apk add --update py-pip
RUN apk add openssl libc-dev python-dev gcc
RUN pip install --upgrade pip
ADD . /usr/src/api
WORKDIR /usr/src/api
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8081

CMD ["python", "/usr/src/api/tw-svc.py"]
