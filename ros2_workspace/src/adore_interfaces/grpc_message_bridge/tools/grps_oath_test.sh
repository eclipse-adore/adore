curl -v -X POST https://supervision.dev-motor-ai.com/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&tenant_id=${TENANT_ID}&fleet_ids=${FLEET_IDS}"
