# Deployment to Google Cloud Run

This document provides the exact commands to deploy the Vera AI Challenge application to Google Cloud Run.

## Prerequisites

1. Install the [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install).
2. Authenticate to your GCP project:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. Enable necessary APIs:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

## Environment Variables

Vera requires a Hosted LLM Provider to run within the 30-second timeout constraints of the Challenge, as local Ollama on a typical serverless container is too slow.

Prepare these environment variables:
- `LLM_PROVIDER=hosted`
- `HOSTED_LLM_URL` (e.g., `https://api.openai.com/v1/chat/completions`)
- `HOSTED_LLM_MODEL` (e.g., `gpt-4o-mini` or `gpt-3.5-turbo`)
- `HOSTED_LLM_API_KEY` (Your provider API key)

## Deployment Command

Run the following command from the root of the repository to build and deploy directly to Cloud Run:

```bash
gcloud run deploy vera-ai-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="LLM_PROVIDER=hosted,HOSTED_LLM_URL=YOUR_URL,HOSTED_LLM_MODEL=YOUR_MODEL" \
  --set-secrets="HOSTED_LLM_API_KEY=YOUR_SECRET_MANAGER_KEY:latest" \
  --timeout=35s \
  --memory=1024Mi
```

*(Note: If you don't use Secret Manager, you can pass `--set-env-vars="HOSTED_LLM_API_KEY=YOUR_KEY"` but it is less secure.)*

## Verifying Deployment

Once deployed, Google Cloud Run will provide a public HTTPS URL (e.g., `https://vera-ai-agent-xxxxx-uc.a.run.app`).

Verify health:
```bash
curl https://vera-ai-agent-xxxxx-uc.a.run.app/v1/healthz
```
