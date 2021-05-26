#!/bin/bash

docker rm -f db
docker-compose -f docker-compose-python-psql.yml up --build --no-deps db
