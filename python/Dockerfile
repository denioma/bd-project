# 
# Bases de Dados 2020/2021
# Trabalho Prático
#
# Authors: 
#   Nuno Antunes <nmsa@dei.uc.pt>
#   BD 2021 Team - https://dei.uc.pt/lei/
#   University of Coimbra

FROM python:3.9-alpine

# Install cryptography dependencies
# RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev libffi-dev openssl-dev cargo

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN python3 -m pip install --upgrade pip

RUN pip install flask

RUN pip install psycopg2-binary

# RUN pip install cryptography

# RUN pip install jwt

COPY . /app

VOLUME ["/app"]

WORKDIR /app

RUN mkdir -p logs

EXPOSE 5000

# CMD ["python", "demo-api.py"]

CMD ["python", "test.py"]
