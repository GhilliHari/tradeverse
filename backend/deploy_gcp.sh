#!/usr/bin/env bash
# ==============================================================================
# 🚀 TRADEVERSE 24/7 GCP CLOUD DEPLOYMENT AUTOMATION SCRIPT
# ==============================================================================

set -e

# Auto-detect active gcloud project or fallback to tradeverse-fe8ef
ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "tradeverse-fe8ef")
PROJECT_ID="${1:-$ACTIVE_PROJECT}"
REGION="${2:-asia-south1}"
ZONE="${3:-asia-south1-a}"
VM_NAME="tradeverse-cloud-node"

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    PROJECT_ID="tradeverse-fe8ef"
fi

echo "======================================================================"
echo "☁️ PROVISIONING 24/7 GCP COMPUTE ENGINE VM FOR PROJECT: ${PROJECT_ID}"
echo " Region: ${REGION} | Zone: ${ZONE} | VM Name: ${VM_NAME}"
echo "======================================================================"

# 1. Create Static External IP for Angel One Broker Whitelisting
echo "📍 Step 1: Reserving Static External IP for Angel One Broker Whitelisting..."
gcloud compute addresses create tradeverse-static-ip --region=${REGION} --project=${PROJECT_ID} || true

STATIC_IP=$(gcloud compute addresses describe tradeverse-static-ip --region=${REGION} --project=${PROJECT_ID} --format='value(address)' 2>/dev/null || echo "FETCHING...")
echo "✅ Reserved Static IP: ${STATIC_IP}"

# 2. Create e2-standard-2 Compute Engine VM (Always-On)
echo "🖥️ Step 2: Provisioning Compute Engine VM (${VM_NAME})..."
gcloud compute instances create ${VM_NAME}     --project=${PROJECT_ID}     --zone=${ZONE}     --machine-type=e2-standard-2     --network-interface=address=${STATIC_IP},network-tier=PREMIUM     --image-family=ubuntu-2204-lts     --image-project=ubuntu-os-cloud     --boot-disk-size=50GB     --tags=http-server,https-server || true

# 3. Configure Firewall Rules for API Port 8000
echo "🛡️ Step 3: Configuring GCP Firewall Rules..."
gcloud compute firewall-rules create allow-tradeverse-api     --project=${PROJECT_ID}     --allow=tcp:8000,tcp:80,tcp:443     --target-tags=http-server     --description="Allow incoming API traffic to Tradeverse Engine" || true

echo "======================================================================"
echo "🎉 24/7 GCP CLOUD INFRASTRUCTURE READY!"
echo " • Target Project ID: ${PROJECT_ID}"
echo " • Reserved Static External IP: ${STATIC_IP}"
echo " • Next Step: Whitelist ${STATIC_IP} in Angel One SmartAPI Developer Portal."
echo "======================================================================"
