# Krateo Autopilot

Krateo autopilot implementation using Google ADK.

# Installation

1. Create a secret containing your Github token.

```bash
kubectl create secret generic github-token --from-literal=token=<your_token>
```

2. Create a Google Cloud Service Account for Vertex AI

- Go to the Google Cloud console and switch to the project where you’ll use Vertex AI.
- Left menu → IAM & Admin → Service Accounts → Create service account.
- Enter a Service account name and (optional) description. Click Create and continue.
- Add the Vertex AI User role.
- Click Continue.
- Click Done.

3. Create a secret for your Google Vertex AI credentials

```bash
kubectl create secret generic gcloud-credentials --from-file=~/.config/gcloud/application_default_credentials.json
```

4. Apply the resources in your cluster 

```bash
kubectl apply -f manifests/
```
