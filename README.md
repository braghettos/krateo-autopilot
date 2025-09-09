# Krateo Autopilot

Krateo Autopilot implementation using Google ADK.

# Installation

## 1. Create a secret containing your Github token.

```bash
# Replace <your_token> with your GitHub Personal Access Token
kubectl create secret generic github-token \
  --from-literal=token=<your_token>
```

## 2. Create Google Cloud Service Account & Key

1. Navigate to the IAM & Admin > Service Accounts page in the Google Cloud Console.
3. Click CREATE SERVICE ACCOUNT.
4. Enter a Service account name and an optional description.
5. Click CREATE AND CONTINUE.
6. Click the SELECT A ROLE field and select Vertex AI User.
7. Click CONTINUE, then click DONE.
8. After the account is created, you need its key. Find the new service account in the list, click the three-dot menu (⋮) under Actions, and select Manage keys.
9. Click ADD KEY > Create new key.
10. Select JSON as the key type and click CREATE. A JSON file containing the key will be downloaded.

## 3. Create a secret for your Google Vertex AI credentials

Now, create a Kubernetes secret from the JSON key file you downloaded in the previous step. This authenticates Autopilot with Google Cloud.

```bash
# Path to your downloaded service account key JSON file
kubectl create secret generic gcloud-credentials \
  --from-file=key.json=<path_to_your_downloaded_key.json>
```

## 4. Deploy Krateo Autopilot

```bash
kubectl apply -f manifests/
```
