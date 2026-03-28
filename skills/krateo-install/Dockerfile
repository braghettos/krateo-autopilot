FROM alpine:3.20

RUN apk add --no-cache bash curl tar

# Install helm
RUN HELM_VERSION=v3.17.1 && \
    curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" -o helm.tar.gz && \
    tar -xzf helm.tar.gz linux-amd64/helm && \
    mv linux-amd64/helm /usr/local/bin/helm && \
    rm -rf helm.tar.gz linux-amd64

# Install kubectl
RUN KUBECTL_VERSION=v1.33.0 && \
    curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" -o kubectl && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

WORKDIR /skill

COPY SKILL.md .
COPY scripts/ ./scripts/

RUN chmod +x scripts/install_krateo.sh
