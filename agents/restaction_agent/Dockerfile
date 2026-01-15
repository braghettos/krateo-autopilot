FROM python:3.13-slim

# Install dependencies for Helm and kubectl
RUN set -euo pipefail && \
apt-get update && apt-get install -y --no-install-recommends \
curl \
bash \
tar \
gzip \
ca-certificates \
&& rm -rf /var/lib/apt/lists/*

# # Install Helm
# RUN set -euo pipefail && \
# curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl
RUN set -euo pipefail && \
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
&& install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
&& rm kubectl

# # Install krateoctl
# RUN curl -sL https://raw.githubusercontent.com/krateoplatformops/krateoctl/main/install.sh 0.8.9 | bash

RUN adduser --disabled-password --gecos "" autopilot
USER autopilot
ENV PATH="/home/autopilot/.local/bin:$PATH"
WORKDIR /app

COPY --chown=autopilot:autopilot agents/restaction_agent/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=autopilot:autopilot agents/restaction_agent/__init__.py __init__.py
COPY --chown=autopilot:autopilot agents/restaction_agent/agent.py agent.py
COPY --chown=autopilot:autopilot agents/config.py config.py

ARG AGENT_NAME="restaction_agent"
COPY --chown=autopilot:autopilot descriptions/eng/${AGENT_NAME}.md descriptions/eng/${AGENT_NAME}.md
COPY --chown=autopilot:autopilot descriptions/ita/${AGENT_NAME}.md descriptions/ita/${AGENT_NAME}.md
COPY --chown=autopilot:autopilot prompts/eng/${AGENT_NAME}.md prompts/eng/${AGENT_NAME}.md
COPY --chown=autopilot:autopilot prompts/ita/${AGENT_NAME}.md prompts/ita/${AGENT_NAME}.md

# Temporary monkey patch to enable a2a streaming
# COPY --chown=autopilot:autopilot agents/to_a2a.py /home/autopilot/lib/python3.13/site-packages/google/adk/a2a/utils/agent_to_a2a.py

CMD ["sh", "-c", "uvicorn agent:a2a_app --host 0.0.0.0 --port ${PORT}"]