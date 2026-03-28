# krateo-install

## Description

Installs Krateo PlatformOps on the current Kubernetes cluster using Helm.

## When to Use

Use this skill when the user asks to:
- Install Krateo on the cluster
- Set up Krateo PlatformOps
- Deploy Krateo

## Available Scripts

### install_krateo.sh

Installs Krateo PlatformOps using the specified installation method.

**Usage:**
```bash
./scripts/install_krateo.sh <METHOD>
```

**Methods:**
- `0` — Basic installation (NodePort). After installation, the portal is accessible at `localhost:30080`.
- `1` — LoadBalancer with external IP. Use when the cluster provides LoadBalancer services with an external IP.
- `2` — LoadBalancer with external hostname. Use when the cluster provides LoadBalancer services with an external hostname (e.g., EKS).

**Post-installation information files:**
- `scripts/Basic.txt` — Instructions after basic installation.
- `scripts/LoadBalancerExternalIP.txt` — Instructions after LoadBalancer (IP) installation.
- `scripts/LoadBalancerExternalHostName.txt` — Instructions after LoadBalancer (hostname) installation.

## Workflow

1. Ask the user which installation method they prefer (0=Basic, 1=LoadBalancer IP, 2=LoadBalancer Hostname).
2. Run `./scripts/install_krateo.sh <METHOD>`.
3. Read and present the corresponding post-installation instructions file to the user.
4. Inform the user that the admin password can be retrieved with:
   ```bash
   kubectl get secret admin-password -n krateo-system -o jsonpath="{.data.password}" | base64 -d
   ```
