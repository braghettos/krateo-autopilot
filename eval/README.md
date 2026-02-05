# Evaluation

## Prerequisites

1. Open the eval directory:

```
cd eval/
```

2. It is recommended to create a virtual environment to avoid conflicts:

```
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```
pip install -r ../requirements.txt
```

4. Create a `.env` file in the root of the `eval` folder as shown in the `.env.example`:
```
cat <<'EOF' > .env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT="google-cloud-project-id"
GOOGLE_CLOUD_LOCATION="google-cloud-location"
EOF
```

5. Finally, run `gcloud auth application-default login` to login to your Google Cloud account. 

Alternatively, (not recommended) create a service account and add `GOOGLE_CLOUD_CREDENTIALS:"path-to-your-service-account-json"` to the `.env` file. 

## Run Evaluation

```
python3 -m pytest eval/eval.py
```
