#!/bin/bash

docker rm -f db
docker-compose up --build db
