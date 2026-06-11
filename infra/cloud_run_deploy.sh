#!/bin/bash
set -euo pipefail

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION=us-central1
SERVICE_NAME=quantsentinel-backend
IMAGE=gcr.io/${PROJECT_ID}/${SERVICE_NAME}

echo "Building and pushing container..."
gcloud builds submit ./backend --tag ${IMAGE}

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --set-secrets PHOENIX_API_KEY=phoenix-api-key:latest \
  --set-secrets FRED_API_KEY=fred-api-key:latest \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --set-env-vars GOOGLE_CLOUD_LOCATION=${REGION} \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE \
  --set-env-vars PHOENIX_COLLECTOR_ENDPOINT=${PHOENIX_COLLECTOR_ENDPOINT} \
  --set-env-vars PHOENIX_BASE_URL=https://app.phoenix.arize.com \
  --set-env-vars PHOENIX_PROJECT_NAME=quantsentinel \
  --set-env-vars CORS_ORIGINS=${FRONTEND_URL}

echo "Done. Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

