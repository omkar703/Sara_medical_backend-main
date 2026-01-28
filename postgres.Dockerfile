FROM ankane/pgvector:v0.5.1

COPY ./scripts/init-db.sh /docker-entrypoint-initdb.d/01-init.sh

RUN chmod +x /docker-entrypoint-initdb.d/01-init.sh
