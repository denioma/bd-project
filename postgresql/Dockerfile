# 
# Bases de Dados 2020/2021
# Trabalho Prático
#
# Authors: 
#   Nuno Antunes <nmsa@dei.uc.pt>
#   BD 2021 Team - https://dei.uc.pt/lei/
#   University of Coimbra

FROM postgres:latest

ENV POSTGRES_USER admin
ENV POSTGRES_PASSWORD projadmin
ENV POSTGRES_DB auctions

COPY sql/setup.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
