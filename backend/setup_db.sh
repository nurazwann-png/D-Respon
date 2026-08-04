#!/bin/bash
# Run once after Cloud SQL instance is RUNNABLE to create database and user
PROJECT=prestij-nurazwann-smartassist
INSTANCE=drespon-db
REGION=asia-southeast1
DB_NAME=drespon
DB_USER=drespon_user

# Set a password (change this before running)
DB_PASS="DRespon@2025!"

echo "Creating database..."
gcloud sql databases create $DB_NAME --instance=$INSTANCE --project=$PROJECT

echo "Creating user..."
gcloud sql users create $DB_USER --instance=$INSTANCE --project=$PROJECT --password="$DB_PASS"

echo "Creating Serverless VPC Access connector..."
gcloud compute networks vpc-access connectors create drespon-connector \
  --region=$REGION \
  --network=default \
  --range=10.8.0.0/28 \
  --project=$PROJECT

echo "Done. Now set DB_PASS in backend/app.yaml or Secret Manager."
echo "Private IP: $(gcloud sql instances describe $INSTANCE --project=$PROJECT --format='value(ipAddresses[0].ipAddress)')"
