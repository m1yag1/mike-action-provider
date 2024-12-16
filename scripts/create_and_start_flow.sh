#!/bin/bash

# This script creates a Flow and starts it

set -euo pipefail

cd "$(dirname "$0")"

export GLOBUS_SDK_ENVIRONMENT=production

if [ $# -eq 0 ]
then
    echo "No arguments supplied!"
    exit 1
else
    ACTION_URL=$1
fi

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

echo "Creating flow definition with ActionUrl: $ACTION_URL"

flow_id=$(globus flows create --format json "$flow_name" "$flow_def" | jq -r '.id')

echo "Created flow with ID: $flow_id"
echo "Login and consent to the flow"

globus login --flow "$flow_id" --no-local-server

run_id=$(globus flows start --format json "$flow_id" | jq -r '.run_id')
echo "$run_id"

echo "Started a flow run with ID: $flow_run"
echo "View the flow's run progress at: https://app.globus.org/runs/$run_id"
