# Deployment to Render (Free Tier)

This document provides the exact configuration required to deploy the Vera AI Challenge application to Render as a Web Service.

## Overview

- **Render Service Type**: Web Service
- **Runtime Environment**: Docker
- **Build/Start Configuration**: Handled natively via the `Dockerfile`. (No manual start command needed in Render Dashboard, as it uses the Dockerfile `CMD`).

## Health Check Path

Render will automatically determine if your deployment is successful by monitoring the port and optionally a health check path.
- **Health Check Path**: `/v1/healthz`

## Recommended Free-Plan Settings

1. **Plan**: Free
2. **Instance Type**: 512 MB RAM, 0.1 CPU
3. **Region**: Choose the one closest to your target users (e.g., US East / Ohio).
4. **Auto-Deploy**: Yes (if deploying directly from GitHub).

## Required Environment Variables

Render uses the `PORT` environment variable automatically, which our Dockerfile dynamically injects into the Uvicorn command. You **must** provide the following environment variables in the Render Dashboard (under Environment > Environment Variables):

| Key | Value |
|---|---|
| `LLM_PROVIDER` | `hosted` |
| `HOSTED_LLM_URL` | `https://openrouter.ai/api/v1/chat/completions` (or `https://openrouter.ai/api/v1`) |
| `HOSTED_LLM_MODEL` | `openrouter/free` |
| `HOSTED_LLM_API_KEY` | `sk-or-v1-...` (Do NOT commit this to code!) |
| `DATABASE_URL` | `sqlite:///./vera.db` (Default, SQLite will be ephemeral on Render Free) |

## Deployment Steps

1. Push your code to a GitHub/GitLab repository. (Ensure `.env` is ignored by `.gitignore`).
2. Go to your [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** and select **Web Service**.
4. Connect your GitHub/GitLab repository.
5. In the configuration settings:
   - Name: `vera-ai` (or similar)
   - Environment: `Docker`
   - Region: Your preferred region
   - Instance Type: Free
6. Expand **Advanced** and click **Add Environment Variable** to add the required variables listed above.
7. Set the **Health Check Path** to `/v1/healthz`.
8. Click **Create Web Service**.

Render will build the Docker container and start the Uvicorn server, assigning a public URL (e.g., `https://vera-ai-xyz.onrender.com`). You can verify deployment by visiting the health check URL in your browser.
