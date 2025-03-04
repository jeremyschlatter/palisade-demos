#!/bin/bash
set -e

# AWS script to demonstrate disk space management
# This script:
# 1. Launches a small EC2 instance with minimal disk space
# 2. Checks disk space on the instance
# 3. Stops the instance
# 4. Increases the disk space
# 5. Restarts and verifies the increased disk space

# Configuration
INSTANCE_NAME="disk-space-demo"
INSTANCE_TYPE="t2.micro"
AMI_ID="ami-0f8e81a3da6e2510a"  # Amazon Linux 2023 in us-west-1
KEY_NAME="default"   # Replace with your key pair name
INITIAL_DISK_SIZE=8             # Initial EBS volume size in GB
INCREASED_DISK_SIZE=16          # Increased EBS volume size in GB
SECURITY_GROUP="default"        # Use your security group that allows SSH
SSH_USER="ec2-user"
REGION="us-west-1"

echo "Starting disk space demo..."

# Launch EC2 instance with small disk
echo "Launching EC2 instance with ${INITIAL_DISK_SIZE}GB disk..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-groups $SECURITY_GROUP \
  --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":${INITIAL_DISK_SIZE},\"DeleteOnTermination\":true}}]" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
  --region $REGION \
  --output text \
  --query 'Instances[0].InstanceId')

echo "Launched instance: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP address
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text \
  --region $REGION)

echo "Instance is running at $PUBLIC_IP"

# Wait for SSH to be available
echo "Waiting for SSH to be available..."
echo "Checking if port 22 is open..."
nc -zvw 5 $PUBLIC_IP 22

echo "Attempting SSH with verbose output..."
ssh -v -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SSH_USER@$PUBLIC_IP echo "SSH is up"

# Continue waiting with debugging information
MAX_ATTEMPTS=20
ATTEMPT=1
while ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$PUBLIC_IP echo "SSH is up" 2>/dev/null
do
  echo "Waiting for SSH... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
  
  # Check security group
  if [ $ATTEMPT -eq 5 ]; then
    echo "Checking security group configuration..."
    aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION
  fi
  
  # Check system log after a few attempts
  if [ $ATTEMPT -eq 10 ]; then
    echo "Checking instance system log..."
    aws ec2 get-console-output --instance-id $INSTANCE_ID --region $REGION
  fi
  
  ATTEMPT=$((ATTEMPT+1))
  if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "SSH connection failed after $MAX_ATTEMPTS attempts."
    echo "Please check:"
    echo "1. Your security group ($SECURITY_GROUP) allows inbound SSH (port 22)"
    echo "2. Your key pair ($KEY_NAME) exists and is correctly set up"
    echo "3. The instance is fully initialized (check console output)"
    echo ""
    echo "You can manually connect using:"
    echo "ssh -i ~/.ssh/your-key.pem $SSH_USER@$PUBLIC_IP"
    echo ""
    echo "To terminate this instance, run:"
    echo "aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION"
    exit 1
  fi
  
  sleep 10
done

# Check initial disk space
echo -e "\n=== INITIAL DISK SPACE ==="
ssh -o StrictHostKeyChecking=no $SSH_USER@$PUBLIC_IP "df -h /"

# Stop the instance
echo -e "\nStopping instance to modify disk space..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION

# Wait for instance to stop
echo "Waiting for instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID --region $REGION

# Get the volume ID
VOLUME_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
  --output text \
  --region $REGION)

# Modify the volume size
echo "Modifying EBS volume size from ${INITIAL_DISK_SIZE}GB to ${INCREASED_DISK_SIZE}GB..."
aws ec2 modify-volume --volume-id $VOLUME_ID --size $INCREASED_DISK_SIZE --region $REGION

# Wait for volume modification to complete
echo "Waiting for volume modification to complete..."
while true; do
  STATE=$(aws ec2 describe-volumes-modifications \
    --volume-ids $VOLUME_ID \
    --query "VolumesModifications[0].ModificationState" \
    --output text \
    --region $REGION)
  
  if [ "$STATE" = "optimizing" ] || [ "$STATE" = "completed" ]; then
    echo "Volume modification is $STATE"
    break
  fi
  
  echo "Volume modification state: $STATE"
  sleep 10
done

# Start the instance again
echo "Starting instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get the possibly new public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text \
  --region $REGION)

echo "Instance is running again at $PUBLIC_IP"

# Wait for SSH to be available
echo "Waiting for SSH to be available..."
while ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$PUBLIC_IP echo "SSH is up" 2>/dev/null
do
  echo "Waiting for SSH..."
  sleep 10
done

# Check if resize2fs is needed to expand filesystem
echo "Expanding filesystem to use new disk space..."
ssh -o StrictHostKeyChecking=no $SSH_USER@$PUBLIC_IP "sudo growpart /dev/xvda 1 && sudo xfs_growfs -d / || sudo resize2fs /dev/xvda1"

# Check the new disk space
echo -e "\n=== INCREASED DISK SPACE ==="
ssh -o StrictHostKeyChecking=no $SSH_USER@$PUBLIC_IP "df -h /"

echo -e "\nDisk resize demonstration completed successfully!"
echo "Don't forget to terminate the instance when done:"
echo "aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION"
