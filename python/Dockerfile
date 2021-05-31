# Databases - 2020/2021
# Final Project

# Authors: 
#   David Valente Pereira Barros Leitão - 2019223148
#   João António Correia Vaz - 2019218159
#   Rodrigo Alexandre da Mota Machado - 2019218299

FROM python:3.9-alpine

VOLUME ["/app"]

WORKDIR /app

COPY . /app

# Install python, build dependencies
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev libffi-dev openssl-dev cargo

# Install Flask
RUN pip install flask
# Install Psycopg2
RUN pip install psycopg2-binary
#Install PyJWT
RUN pip install pyjwt

RUN mkdir -p logs

EXPOSE 5000

# Run Flask App
CMD ["python", "api.py"]
