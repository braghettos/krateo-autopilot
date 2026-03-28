FROM python:3.12-slim

WORKDIR /app

# Install helm
RUN apt-get update && apt-get install -y curl git && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py schema.py ./

ENV PORT=8080

EXPOSE 8080

CMD ["python", "server.py"]
