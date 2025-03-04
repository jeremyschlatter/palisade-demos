# Creating an AWS Key Pair

## Option 1: Using AWS Console

1. Log into the AWS Management Console
2. Navigate to EC2 service
3. In the left sidebar, under "Network & Security," select "Key Pairs"
4. Click "Create key pair"
5. Enter a name for your key pair
6. Select the file format:
   - `.pem` for OpenSSH (macOS/Linux users)
   - `.ppk` for PuTTY (Windows users)
7. Click "Create key pair"
8. The private key file will be automatically downloaded
9. Store this file securely (typically in `~/.ssh/` directory)
10. Set the correct permissions: `chmod 400 ~/.ssh/your-key-name.pem`

## Option 2: Using AWS CLI

1. Install AWS CLI if not already installed
2. Configure AWS CLI with your credentials
3. Run the following command:

```bash
aws ec2 create-key-pair --key-name YourKeyName --query 'KeyMaterial' --output text > ~/.ssh/YourKeyName.pem
```

4. Set the correct permissions:

```bash
chmod 400 ~/.ssh/YourKeyName.pem
```

## Using Your Key Pair with the Demo Scripts

1. Update the demo script with your key pair name:
   - In `aws-disk-demo.sh`: Change `KEY_NAME="your-key-pair-name"` to your key pair name
   - In `aws-disk-demo.py`: Change `self.key_name = "your-key-pair-name"` and `self.key_file = os.path.expanduser("~/.ssh/id_rsa")` to your key file path

2. Make sure your AWS CLI is configured with credentials that have permission to create EC2 instances and modify volumes

3. Your security group (default is "default") must allow SSH (port 22) traffic