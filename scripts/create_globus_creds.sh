#!/bin/bash

# This script creates a Globus project, client id, client secret
# and scope for usage with Action Provider Tools.
# The script assumes whoever is running the it is an admin.
# The output will be a `local.env` file used by the action provider
# to start the web server application.

set -euo pipefail

cd "$(dirname "$0")"

export GLOBUS_SDK_ENVIRONMENT=production

if [ $# -eq 0 ]
then
    echo "No arguments supplied!"
    exit 1
else
    GLOBUS_PROJECT_NAME=$1
fi

if ! globus session show &> /dev/null; then
    echo "Before running the script you must be logged in to globus, please run:"
    echo "globus login"
    exit 1
fi

# GLOBUS_USER_NAME=$(globus whoami --format json | jq -r '.identity_set[0].username')
GLOBUS_USER_ID=$(globus whoami --format json | jq -r '.identity_set[0].sub')
GLOBUS_USER_EMAIL=$(globus whoami --format json | jq -r '.identity_set[0].email')
GLOBUS_CLIENT_ID_NAME="Client for $GLOBUS_PROJECT_NAME"

# Grant consent to the CLI
globus session consent urn:globus:auth:scope:auth.globus.org:manage_projects

project_body=$(cat <<EOF
{
    "project": {
        "display_name": "$GLOBUS_PROJECT_NAME",
        "contact_email": "$GLOBUS_USER_EMAIL",
        "admin_ids": ["$GLOBUS_USER_ID"]
    }
}
EOF
)

echo "Creating Globus project with name [$GLOBUS_PROJECT_NAME]"
GLOBUS_PROJECT_ID=$(globus api auth --content-type json --body "$project_body" POST /v2/api/projects | jq -r '.project.id')
echo "Successfully created project with ID [$GLOBUS_PROJECT_ID]"

client_body=$(cat <<EOF
{
    "client": {
        "name": "$GLOBUS_CLIENT_ID_NAME",
        "project": "$GLOBUS_PROJECT_ID",
        "public_client": false
    }
}
EOF
)

echo "Creating a Client ID for Project ID [$GLOBUS_PROJECT_ID]"
GLOBUS_CLIENT_ID=$(globus api auth --content-type json --body "$client_body" POST /v2/api/clients | jq -r '.client.id')
echo "Successfully created Client ID [$GLOBUS_CLIENT_ID]"

echo "Creating a Client Secret for Client ID [$GLOBUS_CLIENT_ID]"
GLOBUS_CLIENT_SECRET=$(globus api auth --content-type json --body '{"credential": {"name": "'"${GLOBUS_CLIENT_ID_NAME}"'"}}' POST "/v2/api/clients/${GLOBUS_CLIENT_ID}/credentials" | jq -r '.credential.secret')
echo "Successfully created Client Secret"

echo "Creating local.env file ..."

output_body=$(cat <<EOF
# Flask
# ------------------------------------------
# Necessary so Flask can find the application callable.
FLASK_APP=wsgi:app
# Sets Flask's web server to debug mode.
# Interative debugger enabled
# Reload on code changes enabled
# Do not use in production.
FLASK_DEBUG=1

# Globus
# ------------------------------------------
GLOBUS_CLIENT_ID=$GLOBUS_CLIENT_ID
GLOBUS_CLIENT_SECRET=$GLOBUS_CLIENT_SECRET
EOF
)

echo "$output_body" > ../local.env

echo "Creating a scope for your client"

scope_def=$(cat <<EOF
{
    "scope": {
        "name": "$GLOBUS_CLIENT_ID_NAME Scope",
        "description": "All Operations on $GLOBUS_PROJECT_NAME",
        "scope_suffix": "action_all",
        "dependent_scopes": [
            {
                "optional": false,
                "requires_refresh_token": true,
                "scope": "73320ffe-4cb4-4b25-a0a3-83d53d59ce4f"
            }
        ],
        "advertised": true,
        "allow_refresh_tokens": true
    }
}
EOF
)

GLOBUS_SCOPE_ID=$(globus api auth --content-type json --body "$scope_def" POST /v2/api/clients/$GLOBUS_CLIENT_ID/scopes | jq -r '.scopes[0].id')

echo "Successfully created scope with ID [$GLOBUS_SCOPE_ID]"

echo "Script completed successfully."
echo "See the README.md for more information on next steps."

exit 1
