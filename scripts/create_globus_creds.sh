#!/bin/bash

# This script creates a Globus project, client id, client secret
# and scope for usage with Action Provider Tools.
# The script assumes whoever is running the it is an admin.
# The output will be a `local.env` file used by the action provider
# to start the web server application.

set -euo pipefail

cd "$(dirname "$0")"

# Default environment
GLOBUS_SDK_ENVIRONMENT="production"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            GLOBUS_SDK_ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            GLOBUS_PROJECT_NAME="$1"
            shift
            ;;
    esac
done

# Check if project name was provided
if [ -z "${GLOBUS_PROJECT_NAME:-}" ]; then
    echo "No project name supplied!"
    echo "Usage: $0 [-e|--environment ENV] PROJECT_NAME"
    exit 1
fi

# Get scope ID based on environment
case "$GLOBUS_SDK_ENVIRONMENT" in
    "production")
        SCOPE_ID="73320ffe-4cb4-4b25-a0a3-83d53d59ce4f"
        ;;
    "sandbox")
        SCOPE_ID="a9c7ef6f-3858-40fc-a238-551fcef1e7ef"
        ;;
    *)
        echo "Invalid environment: $GLOBUS_SDK_ENVIRONMENT"
        echo "Valid environments are: production, sandbox"
        exit 1
        ;;
esac

export GLOBUS_SDK_ENVIRONMENT

# Check if the user is logged in to globus
if ! uv run globus session show &> /dev/null; then
    echo "Before running the script you must be logged in to globus, please run:"
    uv run globus login
fi

# GLOBUS_USER_NAME=$(globus whoami --format json | jq -r '.identity_set[0].username')
GLOBUS_USER_ID=$(uv run globus whoami --format json | jq -r '.identity_set[0].sub')
GLOBUS_USER_EMAIL=$(uv run globus whoami --format json | jq -r '.identity_set[0].email')
GLOBUS_CLIENT_ID_NAME="Client for $GLOBUS_PROJECT_NAME"

# Grant consent to the CLI
uv run globus session consent urn:globus:auth:scope:auth.globus.org:manage_projects

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
GLOBUS_PROJECT_ID=$(uv run globus api auth --content-type json --body "$project_body" POST /v2/api/projects | jq -r '.project.id')
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
GLOBUS_CLIENT_ID=$(uv run globus api auth --content-type json --body "$client_body" POST /v2/api/clients | jq -r '.client.id')
echo "Successfully created Client ID [$GLOBUS_CLIENT_ID]"

echo "Creating a Client Secret for Client ID [$GLOBUS_CLIENT_ID]"
GLOBUS_CLIENT_SECRET=$(uv run globus api auth --content-type json --body '{"credential": {"name": "'"${GLOBUS_CLIENT_ID_NAME}"'"}}' POST "/v2/api/clients/${GLOBUS_CLIENT_ID}/credentials" | jq -r '.credential.secret')
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

echo "$output_body" > "../local.${GLOBUS_SDK_ENVIRONMENT}.env"

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
                "scope": "$SCOPE_ID"
            }
        ],
        "advertised": true,
        "allow_refresh_tokens": true
    }
}
EOF
)

GLOBUS_SCOPE_ID=$(uv run globus api auth --content-type json --body "$scope_def" POST "/v2/api/clients/$GLOBUS_CLIENT_ID/scopes" | jq -r '.scopes[0].id')

echo "Successfully created scope with ID [$GLOBUS_SCOPE_ID]"

echo "Script completed successfully."
echo "See the README.md for more information on next steps."

exit 1
