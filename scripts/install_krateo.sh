#!/bin/bash

set -euo pipefail

METHOD=$1

echo "Selected installation method: $METHOD"

# Set conditional flags based on the installation method
SET_FLAGS=""

case "$METHOD" in
  0)
    SET_FLAGS=""
    ;;
  1)
    SET_FLAGS="--set krateoplatformops.service.type=LoadBalancer --set krateoplatformops.service.externalIpAvailable=true"
    ;;
  2)
    SET_FLAGS="--set krateoplatformops.service.type=LoadBalancer --set krateoplatformops.service.externalIpAvailable=false"
    ;;
  *)
    echo "Invalid method: $METHOD"
    echo "Valid options: Basic=0, LoadBalancerExternalIP=1, LoadBalancerExternalHostName=2"
    exit 1
    ;;
esac

helm repo add krateo https://charts.krateo.io
helm repo update krateo

helm upgrade installer installer \
  --repo https://charts.krateo.io \
  --namespace krateo-system \
  --create-namespace \
  --set krateoplatformops.composablefinops.enabled=false \
  $SET_FLAGS \
  --install \
  --version 2.5.1 \
  --wait
