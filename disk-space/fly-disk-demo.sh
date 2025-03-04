#!/bin/bash
set -e

# Fly.io script to demonstrate disk space management
# This script:
# 1. Creates a small VM with minimal disk space
# 2. Checks disk space on the VM
# 3. Creates and attaches a volume
# 4. Extends the volume size
# 5. Verifies the increased disk space

# Configuration
APP_NAME="disk-space-demo"
REGION="sjc"  # Silicon Valley
INITIAL_VOLUME_SIZE=1  # GB
INCREASED_VOLUME_SIZE=3  # GB
VOLUME_NAME="data"
AUTO_CLEANUP=${AUTO_CLEANUP:-false}  # Set to true to automatically clean up resources

# Function to check for dependencies
check_dependencies() {
  echo "Checking dependencies..."
  
  # Check for required commands
  local REQUIRED_COMMANDS=("flyctl" "jq" "grep" "sed" "awk")
  local MISSING_COMMANDS=()
  
  for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
      MISSING_COMMANDS+=("$cmd")
    fi
  done
  
  if [ ${#MISSING_COMMANDS[@]} -gt 0 ]; then
    echo "Error: The following required commands are missing:"
    for cmd in "${MISSING_COMMANDS[@]}"; do
      echo "  - $cmd"
    done
    echo ""
    echo "Please install the missing dependencies and try again."
    echo "For flyctl: curl -L https://fly.io/install.sh | sh"
    echo "For jq: Use your package manager (apt, brew, etc.) to install jq"
    exit 1
  fi
  
  echo "All required commands are available."
}

# Function to check if flyctl is installed
check_prerequisites() {
  echo "Checking prerequisites..."
  
  # First check all dependencies
  check_dependencies
  
  # Check if user is authenticated
  if ! flyctl auth whoami &> /dev/null; then
      echo "Error: Not authenticated with Fly.io"
      echo "Please authenticate with Fly.io first:"
      echo "flyctl auth login"
      exit 1
  fi
  
  # Check if user has permissions to create apps
  # This is a simple heuristic - if they can list apps, they likely have permissions
  if ! flyctl apps list &> /dev/null; then
      echo "Error: Unable to list Fly.io apps. You may not have sufficient permissions."
      echo "Please check your Fly.io account and authentication."
      exit 1
  fi
  
  # Check for existing directory that might conflict
  if [ -d "fly-app" ] && [ "$(ls -A fly-app 2>/dev/null)" ]; then
      echo "Warning: 'fly-app' directory already exists and is not empty."
      # If AUTO_CONFIRM is set, don't prompt
      if [ "${AUTO_CONFIRM:-false}" != "true" ]; then
          read -p "This script will modify its contents. Continue? [y/N] " -n 1 -r
          echo
          if [[ ! $REPLY =~ ^[Yy]$ ]]; then
              echo "Aborting."
              exit 1
          fi
      else
          echo "AUTO_CONFIRM is set, continuing without prompt..."
      fi
  fi
  
  echo "Prerequisites check completed successfully."
  
  # Display cleanup behavior
  if [ "$AUTO_CLEANUP" = true ]; then
    echo "Auto cleanup is ENABLED. Resources will be automatically cleaned up after completion."
  else
    echo "Auto cleanup is DISABLED. You will need to manually clean up resources after completion."
    echo "To enable auto cleanup, run with: AUTO_CLEANUP=true $0"
  fi
}

# Function to create and deploy the app
setup_app() {
  echo "Starting Fly.io disk space demo..."

  # Check if app already exists
  if flyctl apps list | grep -q "$APP_NAME"; then
      echo "App $APP_NAME already exists, destroying it first..."
      flyctl apps destroy "$APP_NAME" --yes
      # Give some time for cleanup
      sleep 5
  fi

  # Create a volume first (before creating the app)
  echo "Creating a ${INITIAL_VOLUME_SIZE}GB volume..."
  # Check if volume already exists 
  if flyctl volumes list 2>/dev/null | grep -q "$APP_NAME.*$VOLUME_NAME"; then
      echo "Volume $VOLUME_NAME already exists, deleting it first..."
      VOLUME_ID=$(flyctl volumes list --json | jq -r ".[] | select(.App == \"$APP_NAME\" and .Name == \"$VOLUME_NAME\") | .ID")
      if [ -n "$VOLUME_ID" ]; then
        echo "Destroying volume: $VOLUME_ID"
        flyctl volumes destroy "$VOLUME_ID" --yes
        # Give some time for cleanup
        sleep 5
      fi
  fi
  
  # Launch a new Fly app with a small VM
  echo "Creating new Fly.io app: $APP_NAME..."
  flyctl apps create "$APP_NAME" --machines

  echo "Creating a ${INITIAL_VOLUME_SIZE}GB volume..."
  flyctl volumes create "$VOLUME_NAME" \
    --app "$APP_NAME" \
    --region "$REGION" \
    --size "$INITIAL_VOLUME_SIZE" \
    --yes

  # Create a simple Dockerfile for our demo
  echo "Creating Dockerfile..."
  mkdir -p fly-app
  cat > fly-app/Dockerfile <<EOF
FROM alpine:latest
RUN apk add --no-cache bash
WORKDIR /app
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
EOF

  # Create an entrypoint script that keeps the container running
  cat > fly-app/entrypoint.sh <<EOF
#!/bin/bash
echo "Disk space demo container is running"
echo "Run 'flyctl ssh console -a $APP_NAME' to connect"
while true; do
  sleep 3600
done
EOF

  # Create fly.toml configuration with volume mount
  cat > fly-app/fly.toml <<EOF
app = "$APP_NAME"

[build]

[[mounts]]
  source = "$VOLUME_NAME"
  destination = "/data"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
EOF

  # Deploy the app
  echo "Deploying the app..."
  cd fly-app
  flyctl deploy --local-only --regions "$REGION"
  cd ..

  echo "Waiting for deployment to complete..."
  sleep 10
}

# Function to get current machine ID
get_machine_id() {
  # Get the machine ID, with error handling
  MACHINE_ID=$(flyctl machines list -a "$APP_NAME" --json | jq -r '.[0].id')
  
  if [ -z "$MACHINE_ID" ] || [ "$MACHINE_ID" = "null" ]; then
    echo "Error: Failed to get machine ID. Check if the app has any machines running."
    echo "Try listing machines with: flyctl machines list -a $APP_NAME"
    exit 1
  fi
  
  echo "Machine ID: $MACHINE_ID"
  
  # Store original directory to ensure we're always in the project root
  PROJECT_ROOT=$(pwd)
}

# Function to check disk space
check_disk_space() {
  # SSH into the machine to check initial disk space
  echo -e "\n=== INITIAL DISK SPACE ==="
  
  # Try with a timeout and retry if needed
  local ATTEMPTS=0
  local MAX_ATTEMPTS=5  # Increased attempts
  local SUCCESS=false
  
  # Wait a bit longer before first attempt
  echo "Waiting for machine to fully start up..."
  sleep 20
  
  while [ $ATTEMPTS -lt $MAX_ATTEMPTS ] && [ "$SUCCESS" = false ]; do
    echo "Attempt $((ATTEMPTS+1))/$MAX_ATTEMPTS to check disk space..."
    
    # First list all filesystems to debug
    echo "Listing all mounted filesystems:"
    flyctl ssh console -a "$APP_NAME" -C "df -h"
    
    # Then try to access /data specifically
    echo "Checking /data mount:"
    # Run commands separately, ensure we're in the right directory
    cd "$PROJECT_ROOT"
    flyctl ssh console -a "$APP_NAME" -C "ls -la /data" 
    if cd "$PROJECT_ROOT" && flyctl ssh console -a "$APP_NAME" -C "df -h /data"; then
      SUCCESS=true
    else
      ATTEMPTS=$((ATTEMPTS+1))
      if [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; then
        echo "Volume check failed. Waiting 15 seconds before retry ($ATTEMPTS/$MAX_ATTEMPTS)..."
        sleep 15
      fi
    fi
  done
  
  if [ "$SUCCESS" = false ]; then
    echo "Error: Failed to verify /data mount after $MAX_ATTEMPTS attempts."
    echo "The volume might not be properly attached. Continuing anyway to see if volume extension helps..."
    # Don't exit - try to continue with the script
  fi
}

# Function to extend volume size
extend_volume() {
  # First get the volume ID using awk instead of jq
  echo -e "\nGetting volume ID for $VOLUME_NAME..."
  VOLUME_ID=$(flyctl volumes list -a "$APP_NAME" | grep "^vol_" | grep "$VOLUME_NAME" | awk '{print $1}')
  
  if [ -z "$VOLUME_ID" ]; then
    echo "Error: Failed to get volume ID for $VOLUME_NAME. Check if the volume exists."
    echo "Try manually listing volumes with: flyctl volumes list -a $APP_NAME"
    exit 1
  fi
  
  echo "Volume ID: $VOLUME_ID"
  
  # Extend the volume size
  echo -e "\nExtending volume from ${INITIAL_VOLUME_SIZE}GB to ${INCREASED_VOLUME_SIZE}GB..."
  flyctl volumes extend "$VOLUME_ID" \
    --size "$INCREASED_VOLUME_SIZE" \
    --yes

  # Wait for the resize to complete
  echo "Waiting for volume resize to complete..."
  sleep 15
}

# Function to check the new disk space
check_new_disk_space() {
  # Check the new disk space
  echo -e "\n=== INCREASED DISK SPACE ==="
  
  # Wait a bit for the resize to take effect
  echo "Waiting for resize to take effect..."
  sleep 15
  
  # Try with a timeout and retry if needed
  local ATTEMPTS=0
  local MAX_ATTEMPTS=5  # Increased attempts
  local SUCCESS=false
  
  while [ $ATTEMPTS -lt $MAX_ATTEMPTS ] && [ "$SUCCESS" = false ]; do
    echo "Attempt $((ATTEMPTS+1))/$MAX_ATTEMPTS to check new disk space..."
    
    # First list all filesystems to debug
    echo "Listing all mounted filesystems:"
    flyctl ssh console -a "$APP_NAME" -C "df -h"
    
    # Then try to access /data specifically
    echo "Checking /data mount after resize:"
    # Run commands separately, ensure we're in the right directory
    cd "$PROJECT_ROOT" 
    flyctl ssh console -a "$APP_NAME" -C "ls -la /data"
    if cd "$PROJECT_ROOT" && flyctl ssh console -a "$APP_NAME" -C "df -h /data"; then
      SUCCESS=true
    else
      ATTEMPTS=$((ATTEMPTS+1))
      if [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; then
        echo "Volume check failed. Waiting 15 seconds before retry ($ATTEMPTS/$MAX_ATTEMPTS)..."
        sleep 15
      fi
    fi
  done
  
  if [ "$SUCCESS" = false ]; then
    echo "Error: Failed to verify /data mount after resize."
    echo "Try manually running: flyctl ssh console -a $APP_NAME -C \"df -h /data\""
  else
    echo -e "\nDisk resize demonstration completed successfully!"
  fi
  
  if [ "$AUTO_CLEANUP" = true ]; then
    echo -e "\nAutomatic cleanup is enabled. Cleaning up resources..."
    cleanup_resources
  else
    echo -e "\nTo clean up resources, run:"
    echo "flyctl apps destroy $APP_NAME --yes"
    echo "flyctl volumes delete $VOLUME_NAME --app $APP_NAME --yes"
    echo "Or run this script with AUTO_CLEANUP=true to clean up automatically."
  fi
}

# Function to clean up resources
cleanup_resources() {
  echo "Cleaning up resources..."
  
  # Get volume ID for later
  local VOLUME_ID=""
  VOLUME_ID=$(flyctl volumes list --json | jq -r ".[] | select(.App == \"$APP_NAME\" and .Name == \"$VOLUME_NAME\") | .ID")
  
  # Destroy the app
  echo "Destroying app: $APP_NAME"
  echo "y" | flyctl apps destroy "$APP_NAME"
  
  # Check if we need to manually delete volume
  if [ -n "$VOLUME_ID" ]; then
    echo "Destroying volume: $VOLUME_ID"
    echo "y" | flyctl volumes destroy "$VOLUME_ID"
  fi
  
  # Clean up local files
  if [ -d "fly-app" ]; then
    echo "Removing local fly-app directory"
    rm -rf fly-app
  fi
  
  echo "Cleanup completed successfully."
}

# Trap function to handle script interruptions
cleanup_on_error() {
  echo "Script interrupted or error encountered."
  
  if [ "$AUTO_CLEANUP" = true ]; then
    echo "Attempting to clean up resources..."
    cleanup_resources
  else
    echo "You may need to manually clean up resources:"
    echo "flyctl apps destroy $APP_NAME --yes"
    echo "flyctl volumes list # to find any volumes"
    echo "flyctl volumes destroy <volume-id> --yes"
  fi
  
  exit 1
}

# Set up trap for interruptions
trap cleanup_on_error INT TERM ERR

# Parse command-line arguments
if [ "$1" = "--cleanup" ]; then
  AUTO_CLEANUP=true
  shift
fi

# Main execution
check_prerequisites
setup_app
# Save the project root directory for later use
PROJECT_ROOT=$(pwd)

get_machine_id  # Get the machine ID for later use
check_disk_space
extend_volume
check_new_disk_space