#!/bin/bash
set -e

REGISTRY="redi21"
VERSION="${1:-0.0.1}"

# Define agents with their directory paths and image names
declare -A AGENTS=(
  ["remote_agents/auth_agent"]="auth-agent"
  ["remote_agents/blueprint_agent"]="blueprint-agent"
  ["remote_agents/documentation_agent"]="documentation-agent"
  ["remote_agents/portal_agent"]="portal-agent"
  ["remote_agents/restaction_agent"]="restaction-agent"
)

echo "Building and pushing all agents with version: $VERSION"
echo "=========================================="

for agent_path in "${!AGENTS[@]}"; do
  image_name="${AGENTS[$agent_path]}"
  full_image="$REGISTRY/$image_name:$VERSION"
  
  echo ""
  echo "Building $image_name..."
  docker build -f "$agent_path/Dockerfile" -t "$full_image" .
  
  echo "Pushing $full_image..."
  docker push "$full_image"
  
  echo "✓ Completed $image_name"
done

echo ""
echo "=========================================="
echo "All images built and pushed successfully!"