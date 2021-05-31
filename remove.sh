#!/bin/bash

docker compose down

if [ $1 = 'web' ]; then
  docker rmi auction_web
elif [ $1 = 'db' ]; then
  docker rmi auction_db
else
  docker rmi auction_web auction_db
fi  
