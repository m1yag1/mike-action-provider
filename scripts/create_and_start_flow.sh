#!/bin/bash

# This script creates a Flow and starts it

set -euo pipefail

cd "$(dirname "$0")"

# Default environment
GLOBUS_SDK_ENVIRONMENT="production"
SUBSCRIPTION_ID=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            GLOBUS_SDK_ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--subscription_id)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        *)
            ACTION_URL="$1"
            shift
            ;;
    esac
done

# Check if action URL was provided
if [ -z "${ACTION_URL:-}" ]; then
    echo "No action URL supplied!"
    echo "Usage: $0 [-e|--environment ENV] [-s|--subscription_id ID] ACTION_URL"
    exit 1
fi

export GLOBUS_SDK_ENVIRONMENT

flow_def=$(cat <<EOF
{
    "StartAt": "WhatTimeIsIt",
    "States": {
      "WhatTimeIsIt": {
        "Type": "Action",
        "ActionUrl": "$ACTION_URL/apt",
        "Parameters": {"utc_offset": 6},
        "ResultPath": "$.TimeResult",
        "End": true
        }
    }
}
EOF
)

flow_name="WhatTimeIsItFlow"

# Check if the user is logged in to globus
if ! uv run globus session show &> /dev/null; then
    echo "Before running the script you must be logged in to globus, please run:"
    uv run globus login
fi

echo "Creating flow definition with ActionUrl: $ACTION_URL"

CREATE_CMD="globus flows create --format json"

# Update command when a subscription ID is provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    CREATE_CMD="$CREATE_CMD --subscription-id $SUBSCRIPTION_ID"
fi

flow_id=$($CREATE_CMD "$flow_name" "$flow_def" | jq -r '.id')

echo "Created flow with ID: $flow_id"
echo "Login and consent to the flow"

uv run globus login --flow "$flow_id" --no-local-server

run_id=$(uv run globus flows start --format json "$flow_id" | jq -r '.run_id')
echo "$run_id"

echo "Started a flow run with ID: $run_id"

# Get the base URL based on environment
if [ "$GLOBUS_SDK_ENVIRONMENT" = "production" ]; then
    BASE_URL="https://app.globus.org"
else
    BASE_URL="https://app.${GLOBUS_SDK_ENVIRONMENT}.globuscs.info"
fi

echo "View the flow's run progress at: ${BASE_URL}/runs/$run_id"
