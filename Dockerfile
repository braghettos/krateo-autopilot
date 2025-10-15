FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies for Helm and kubectl
RUN set -euo pipefail && \
apt-get update && apt-get install -y --no-install-recommends \
curl \
bash \
tar \
gzip \
ca-certificates \
&& rm -rf /var/lib/apt/lists/*

# Install Helm
RUN set -euo pipefail && \
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl
RUN set -euo pipefail && \
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
&& install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
&& rm kubectl

# Install krateoctl
RUN curl -sL https://raw.githubusercontent.com/krateoplatformops/krateoctl/main/install.sh | bash

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

COPY . .

RUN chmod +x /app/tools/scripts/install_krateo.sh

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]