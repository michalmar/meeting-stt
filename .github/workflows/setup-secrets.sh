#!/bin/bash

# GitHub Actions Secrets Setup Script
# This script creates all required GitHub secrets for the CI/CD pipeline
# Prerequisites: 
#   - GitHub CLI (gh) must be installed and authenticated
#   - Azure CLI (az) must be installed and authenticated
#   - Run this from the repository root directory

set -e

echo "🔐 Setting up GitHub Secrets for CI/CD..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first."
    echo "   Visit: https://cli.github.com/"
    exit 1
fi

# Check if az CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI (az) is not installed. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Load values from .env file
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env file not found!"
    exit 1
fi

# Source the .env file (remove quotes from values)
echo "📥 Loading configuration from backend/.env..."

# Read .env file and export variables (handle quotes properly)
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^#.* ]] && continue
    
    # Remove quotes from value
    value="${value%\"}"
    value="${value#\"}"
    
    # Export the variable
    export "$key"="$value"
done < backend/.env

# Confirm required variables are set
REQUIRED_VARS=(
  AZURE_SUBSCRIPTION_ID
  AZURE_RESOURCE_GROUP
  AZURE_CONTAINER_REGISTRY_ENDPOINT     
    AZURE_OPENAI_ENDPOINT
    UAMI_RESOURCE_ID
    AZURE_STORAGE_ACCOUNT_ENDPOINT
    AZURE_STORAGE_ACCOUNT_ID
    AZURE_SPEECH_ENDPOINT
    AZURE_SPEECH_REGION
    AZURE_SPEECH_KEY
    MODEL_NAME
    AZURE_OPENAI_ENDPOINT_TRANSCRIBE
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE
    AZURE_STORAGE_ACCOUNT_NAME
    AZURE_STORAGE_ACCOUNT_KEY
    SERVICE_BACKEND_URI
)

for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "❌ Required variable $VAR is not set in backend/.env"
    exit 1
  fi
done

echo "📋 Loaded values from backend/.env"

# Extract registry name from endpoint
REGISTRY_NAME=$(echo $AZURE_CONTAINER_REGISTRY_ENDPOINT | cut -d'.' -f1)

echo "🔍 Using Azure Container Registry: $REGISTRY_NAME"

echo "🔑 Creating Azure Service Principal..."

# Create Service Principal for GitHub Actions
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "github-actions-meeting-stt-$(date +%s)" \
  --role contributor \
  --scopes "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP" \
  --sdk-auth)

echo "✅ Service Principal created"

# Enable ACR admin user if not already enabled
echo "🔐 Enabling ACR admin user..."
az acr update -n $REGISTRY_NAME -g $AZURE_RESOURCE_GROUP --admin-enabled true > /dev/null

# Get ACR credentials
echo "🔑 Retrieving ACR credentials..."
REGISTRY_USERNAME=$(az acr credential show -n $REGISTRY_NAME -g $AZURE_RESOURCE_GROUP --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show -n $REGISTRY_NAME -g $AZURE_RESOURCE_GROUP --query "passwords[0].value" -o tsv)

echo "✅ ACR credentials retrieved"

# Set GitHub secrets
echo ""
echo "📤 Setting GitHub secrets..."

gh secret set AZURE_CREDENTIALS --body "$SP_OUTPUT"
echo "  ✓ AZURE_CREDENTIALS"

gh secret set AZURE_CONTAINER_REGISTRY --body "$AZURE_CONTAINER_REGISTRY_ENDPOINT"
echo "  ✓ AZURE_CONTAINER_REGISTRY"

gh secret set REGISTRY_USERNAME --body "$REGISTRY_USERNAME"
echo "  ✓ REGISTRY_USERNAME"

gh secret set REGISTRY_PASSWORD --body "$REGISTRY_PASSWORD"
echo "  ✓ REGISTRY_PASSWORD"

gh secret set AZURE_RESOURCE_GROUP --body "$AZURE_RESOURCE_GROUP"
echo "  ✓ AZURE_RESOURCE_GROUP"

gh secret set AZURE_SUBSCRIPTION_ID --body "$AZURE_SUBSCRIPTION_ID"
echo "  ✓ AZURE_SUBSCRIPTION_ID"

# Set environment variables needed by the Container App
gh secret set AZURE_OPENAI_ENDPOINT --body "$AZURE_OPENAI_ENDPOINT"
echo "  ✓ AZURE_OPENAI_ENDPOINT"

# Get the managed identity client ID
echo "🔑 Retrieving Managed Identity Client ID..."
MANAGED_IDENTITY_NAME=$(basename "$UAMI_RESOURCE_ID")
AZURE_CLIENT_ID=$(az identity show --ids "$UAMI_RESOURCE_ID" --query clientId -o tsv)

gh secret set AZURE_CLIENT_ID --body "$AZURE_CLIENT_ID"
echo "  ✓ AZURE_CLIENT_ID"

gh secret set AZURE_STORAGE_ACCOUNT_ENDPOINT --body "$AZURE_STORAGE_ACCOUNT_ENDPOINT"
echo "  ✓ AZURE_STORAGE_ACCOUNT_ENDPOINT"

gh secret set AZURE_STORAGE_ACCOUNT_ID --body "$AZURE_STORAGE_ACCOUNT_ID"
echo "  ✓ AZURE_STORAGE_ACCOUNT_ID"

gh secret set UAMI_RESOURCE_ID --body "$UAMI_RESOURCE_ID"
echo "  ✓ UAMI_RESOURCE_ID"

gh secret set AZURE_SPEECH_ENDPOINT --body "$AZURE_SPEECH_ENDPOINT"
echo "  ✓ AZURE_SPEECH_ENDPOINT"

gh secret set AZURE_SPEECH_REGION --body "$AZURE_SPEECH_REGION"
echo "  ✓ AZURE_SPEECH_REGION"

gh secret set AZURE_SPEECH_KEY --body "$AZURE_SPEECH_KEY"
echo "  ✓ AZURE_SPEECH_KEY"

gh secret set MODEL_NAME --body "$MODEL_NAME"
echo "  ✓ MODEL_NAME"

gh secret set AZURE_OPENAI_ENDPOINT_TRANSCRIBE --body "$AZURE_OPENAI_ENDPOINT_TRANSCRIBE"
echo "  ✓ AZURE_OPENAI_ENDPOINT_TRANSCRIBE"

gh secret set AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE --body "$AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE"
echo "  ✓ AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE"

gh secret set AZURE_STORAGE_ACCOUNT_NAME --body "$AZURE_STORAGE_ACCOUNT_NAME"
echo "  ✓ AZURE_STORAGE_ACCOUNT_NAME"

gh secret set AZURE_STORAGE_ACCOUNT_KEY --body "$AZURE_STORAGE_ACCOUNT_KEY"
echo "  ✓ AZURE_STORAGE_ACCOUNT_KEY"

gh secret set SERVICE_BACKEND_URI --body "$SERVICE_BACKEND_URI"
echo "  ✓ SERVICE_BACKEND_URI"

# Get Azure Static Web Apps deployment token
echo "🔑 Retrieving Azure Static Web Apps deployment token..."
STATIC_WEB_APP_NAME=$(az staticwebapp list -g $AZURE_RESOURCE_GROUP --query "[0].name" -o tsv)
if [ -n "$STATIC_WEB_APP_NAME" ]; then
  AZURE_STATIC_WEB_APPS_API_TOKEN=$(az staticwebapp secrets list -n $STATIC_WEB_APP_NAME -g $AZURE_RESOURCE_GROUP --query "properties.apiKey" -o tsv)
  gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "$AZURE_STATIC_WEB_APPS_API_TOKEN"
  echo "  ✓ AZURE_STATIC_WEB_APPS_API_TOKEN"
else
  echo "  ⚠️  Static Web App not found. Please set AZURE_STATIC_WEB_APPS_API_TOKEN manually."
  echo "     Get it from: Azure Portal → Static Web App → Manage deployment token"
fi

echo ""
echo "✅ All GitHub secrets have been created successfully!"
echo ""
echo "🎉 Your CI/CD pipeline is now ready to use."
echo ""
echo "To verify the secrets, run:"
echo "  gh secret list"
echo ""
echo "To trigger a deployment, push changes to the main branch or run:"
echo "  gh workflow run deploy-backend.yml"
