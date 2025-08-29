# google-adk
Krateo autopilot implementation using Google ADK

# Installation

1. Create a secret containing your Github token.

```bash
kubectl create secret generic github-token --from-literal=token=<your_token>
```

2. Create a secret for your Google Vertex AI credentials

First create a service account from Google Cloud's UI. Then create the secret.

```bash
kubectl create secret generic gcloud-credentials --from-file=~/.config/gcloud/application_default_credentials.json
```

3. Apply the resources in your cluster 

```bash
kubectl apply -f manifests/
```
