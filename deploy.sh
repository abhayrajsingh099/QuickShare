
#!/usr/bin/env bash
set -Eeuo pipefail

# QuickShare production deployment

BRANCH="main"
LOCAL_ENV_FILE=".envs/.env.production"
REMOTE_PROJECT_DIR=""

echo "================================"
echo "   QuickShare Deployment"
echo "================================"

# Check local production environment file
if [[ ! -f "$LOCAL_ENV_FILE" ]]; then
    echo "ERROR: $LOCAL_ENV_FILE does not exist."
    exit 1
fi

# Collect EC2 connection details
read -r -p "EC2 public IP or DNS: " EC2_HOST
read -r -p "SSH username [ubuntu]: " SSH_USER
SSH_USER="${SSH_USER:-ubuntu}"

read -r -p "SSH private key path: " SSH_KEY

if [[ -z "$EC2_HOST" || -z "$SSH_KEY" ]]; then
    echo "ERROR: EC2 host and SSH key are required."
    exit 1
fi

if [[ ! -f "$SSH_KEY" ]]; then
    echo "ERROR: SSH key not found: $SSH_KEY"
    exit 1
fi

SSH_TARGET="${SSH_USER}@${EC2_HOST}"
REMOTE_PROJECT_DIR="/home/${SSH_USER}/apps/QuickShare"

echo
echo "Target: $SSH_TARGET"
echo "Remote directory: $REMOTE_PROJECT_DIR"
echo "Branch: $BRANCH"
echo

# Restrict local environment file permissions
chmod 600 "$LOCAL_ENV_FILE"

# Prepare remote environment directory
echo "[1/5] Preparing EC2..."

ssh -i "$SSH_KEY" -o IdentitiesOnly=yes "$SSH_TARGET" \
    "mkdir -p '$REMOTE_PROJECT_DIR/.envs' &&
     chmod 700 '$REMOTE_PROJECT_DIR/.envs'"

# Transfer backend production secrets
echo "[2/5] Transferring production environment file..."

scp -i "$SSH_KEY" -o IdentitiesOnly=yes \
    "$LOCAL_ENV_FILE" \
    "$SSH_TARGET:$REMOTE_PROJECT_DIR/.envs/.env.production.upload"

# Install environment file, update code and validate configuration
echo "[3/5] Pulling latest code and validating configuration..."

ssh -t -i "$SSH_KEY" -o IdentitiesOnly=yes "$SSH_TARGET" "
    set -e
    cd '$REMOTE_PROJECT_DIR'

    chmod 600 .envs/.env.production.upload
    mv .envs/.env.production.upload .envs/.env.production

    git fetch origin
    git checkout '$BRANCH'
    git pull --ff-only origin '$BRANCH'

    sudo docker compose \
        --env-file .envs/.env.production \
        -f production.yml config --quiet

    echo 'Configuration validation passed.'
"

# Build and start production containers
echo "[4/5] Building and starting production containers..."

ssh -t -i "$SSH_KEY" -o IdentitiesOnly=yes "$SSH_TARGET" "
    set -e
    cd '$REMOTE_PROJECT_DIR'

    sudo docker compose \
        --env-file .envs/.env.production \
        -f production.yml up -d --build
"

# Check container status and report failures
echo "[5/5] Checking container status..."

ssh -t -i "$SSH_KEY" -o IdentitiesOnly=yes "$SSH_TARGET" "
    cd '$REMOTE_PROJECT_DIR'

    sudo docker compose \
        --env-file .envs/.env.production \
        -f production.yml ps

    echo
    echo 'Checking for exited containers...'

    FAILED=\$(sudo docker compose \
        --env-file .envs/.env.production \
        -f production.yml ps --all --format json |
        python3 -c '
import json, sys
data = sys.stdin.read().strip()
containers = [json.loads(line) for line in data.splitlines() if line.strip()]
failed = [c for c in containers if c.get(\"State\", \"\").lower() in (\"exited\", \"dead\")]
print(len(failed))
')

    if [ \"\$FAILED\" -gt 0 ]; then
        echo 'ERROR: Some containers have exited or died.'
        sudo docker compose \
            --env-file .envs/.env.production \
            -f production.yml logs --tail=100
        exit 1
    fi

    echo 'No exited or dead containers detected.'
"

echo
echo "================================"
echo " Deployment command completed."
echo " Verify service health and API."
echo "================================"
