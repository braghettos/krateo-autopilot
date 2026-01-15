# Krateo Autopilot

Krateo Autopilot implementation using Google ADK.

# Installation


## 1. Create Google Cloud Service Account & Key

1. Navigate to the IAM & Admin > Service Accounts page in the Google Cloud Console.
3. Click CREATE SERVICE ACCOUNT.
4. Enter a Service account name and an optional description.
5. Click CREATE AND CONTINUE.
6. Click the SELECT A ROLE field and select Vertex AI User.
7. Click CONTINUE, then click DONE.
8. After the account is created, you need its key. Find the new service account in the list, click the three-dot menu (⋮) under Actions, and select Manage keys.
9. Click ADD KEY > Create new key.
10. Select JSON as the key type and click CREATE. A JSON file containing the key will be downloaded.

## 2. Create a secret for your Google Vertex AI credentials

Now, create a Kubernetes secret from the JSON key file you downloaded in the previous step. This authenticates Autopilot with Google Cloud.

```bash
kubectl create secret generic gcloud-credentials \
  --from-file=key.json=<path_to_your_downloaded_key.json>
```

## 3. Install CloudNativePG's Operator

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.1.yaml
```

> Note: The DB is used for enabling persistent sessions; you can skip this step and disable them by adding the `--set database.enabled=false` flag in the chart installation.

## 4. Install the Chart

```bash
helm repo add krateo https://charts.krateo.io
helm repo update krateo
helm install autopilot krateo/autopilot \
  --set env.GOOGLE_CLOUD_PROJECT=<google-cloud-project-ID> \
```
