# Databases - 2020/2021
# Final Project

# Authors: 
#   David Valente Pereira Barros Leitão - 2019223148
#   João António Correia Vaz - 2019218159
#   Rodrigo Alexandre da Mota Machado - 2019218299

FROM postgres:latest

ENV POSTGRES_USER admin
ENV POSTGRES_PASSWORD projadmin
ENV POSTGRES_DB auctions

COPY sql/setup.sql /docker-entrypoint-initdb.d/

COPY sql/triggers.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
