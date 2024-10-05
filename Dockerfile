FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates

RUN wget -qO - https://pgp.mongodb.com/server-6.0.asc | tee /etc/apt/trusted.gpg.d/mongodb.asc

RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

RUN apt-get update && apt-get install -y mongodb-mongosh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash"]