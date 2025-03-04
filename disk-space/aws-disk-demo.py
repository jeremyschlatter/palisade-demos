#!/usr/bin/env python3

import boto3
import paramiko
import time
import sys
import os


class DiskSpaceDemo:
    def __init__(self):
        # Configuration
        self.instance_name = "disk-space-demo"
        self.instance_type = "t2.micro"
        self.ami_id = "ami-0df435f331839b2d6"  # Amazon Linux 2023 in us-east-1
        self.key_name = "your-key-pair-name"   # Replace with your key pair name
        self.initial_disk_size = 8             # Initial EBS volume size in GB
        self.increased_disk_size = 16          # Increased EBS volume size in GB
        self.security_group = "default"        # Use your security group that allows SSH
        self.ssh_user = "ec2-user"
        self.region = "us-east-1"
        self.key_file = os.path.expanduser("~/.ssh/id_rsa")  # Path to your private key file
        
        # Initialize AWS clients
        self.ec2 = boto3.resource('ec2', region_name=self.region)
        self.ec2_client = boto3.client('ec2', region_name=self.region)
        
        # Store instance ID
        self.instance_id = None
        self.volume_id = None
        self.public_ip = None
        
    def log(self, message):
        """Print a timestamped log message."""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def launch_instance(self):
        """Launch an EC2 instance with a small disk."""
        self.log(f"Launching EC2 instance with {self.initial_disk_size}GB disk...")
        
        instances = self.ec2.create_instances(
            ImageId=self.ami_id,
            InstanceType=self.instance_type,
            KeyName=self.key_name,
            MinCount=1,
            MaxCount=1,
            SecurityGroups=[self.security_group],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': self.initial_disk_size,
                        'DeleteOnTermination': True,
                    }
                }
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': self.instance_name}]
                }
            ]
        )
        
        self.instance_id = instances[0].id
        self.log(f"Launched instance: {self.instance_id}")
        
        # Wait for instance to be running
        self.log("Waiting for instance to be running...")
        instances[0].wait_until_running()
        
        # Reload instance to get public IP
        instance = self.ec2.Instance(self.instance_id)
        self.public_ip = instance.public_ip_address
        self.log(f"Instance is running at {self.public_ip}")
        
        # Get volume ID
        volumes = list(instance.volumes.all())
        if volumes:
            self.volume_id = volumes[0].id
            self.log(f"Instance has volume: {self.volume_id}")
        else:
            raise Exception("Could not find volume attached to instance")
        
    def wait_for_ssh(self):
        """Wait for SSH to be available on the instance."""
        self.log("Waiting for SSH to be available...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        max_retries = 30
        for i in range(max_retries):
            try:
                ssh.connect(
                    self.public_ip, 
                    username=self.ssh_user,
                    key_filename=self.key_file,
                    timeout=5
                )
                ssh.close()
                self.log("SSH is available")
                return
            except (paramiko.ssh_exception.NoValidConnectionsError,
                    paramiko.ssh_exception.SSHException,
                    TimeoutError) as e:
                if i < max_retries - 1:
                    self.log(f"Waiting for SSH... (attempt {i+1}/{max_retries})")
                    time.sleep(10)
                else:
                    raise Exception(f"Failed to connect via SSH after {max_retries} attempts") from e
    
    def run_ssh_command(self, command):
        """Run a command on the instance via SSH."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                self.public_ip, 
                username=self.ssh_user,
                key_filename=self.key_file
            )
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                self.log(f"Error: {error}")
            
            return output
        finally:
            ssh.close()
    
    def check_disk_space(self):
        """Check disk space on the instance."""
        self.log("\n=== CHECKING DISK SPACE ===")
        output = self.run_ssh_command("df -h /")
        self.log(output)
        return output
    
    def resize_volume(self):
        """Stop instance, resize the volume, and start instance again."""
        # Stop the instance
        self.log("Stopping instance to modify disk space...")
        self.ec2_client.stop_instances(InstanceIds=[self.instance_id])
        
        # Wait for instance to stop
        self.log("Waiting for instance to stop...")
        waiter = self.ec2_client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[self.instance_id])
        
        # Modify the volume size
        self.log(f"Modifying EBS volume size from {self.initial_disk_size}GB to {self.increased_disk_size}GB...")
        self.ec2_client.modify_volume(
            VolumeId=self.volume_id,
            Size=self.increased_disk_size
        )
        
        # Wait for volume modification to complete
        self.log("Waiting for volume modification to complete...")
        complete = False
        while not complete:
            response = self.ec2_client.describe_volumes_modifications(VolumeIds=[self.volume_id])
            state = response['VolumesModifications'][0]['ModificationState']
            
            if state in ['optimizing', 'completed']:
                self.log(f"Volume modification is {state}")
                complete = True
            else:
                self.log(f"Volume modification state: {state}")
                time.sleep(10)
        
        # Start the instance again
        self.log("Starting instance...")
        self.ec2_client.start_instances(InstanceIds=[self.instance_id])
        
        # Wait for instance to be running
        self.log("Waiting for instance to be running...")
        waiter = self.ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[self.instance_id])
        
        # Get the possibly new public IP
        response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
        self.public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        self.log(f"Instance is running again at {self.public_ip}")
        
    def expand_filesystem(self):
        """Expand the filesystem to use the new disk space."""
        self.log("Expanding filesystem to use new disk space...")
        
        # Amazon Linux 2023 uses XFS by default, but handle both XFS and ext4
        command = "sudo growpart /dev/xvda 1 && (sudo xfs_growfs -d / || sudo resize2fs /dev/xvda1)"
        output = self.run_ssh_command(command)
        if output:
            self.log(output)
    
    def run_demo(self):
        """Run the full disk space demo."""
        try:
            self.log("Starting disk space demo...")
            
            # Launch instance and check initial disk space
            self.launch_instance()
            self.wait_for_ssh()
            self.log("\n=== INITIAL DISK SPACE ===")
            self.check_disk_space()
            
            # Resize volume and check new disk space
            self.resize_volume()
            self.wait_for_ssh()
            self.expand_filesystem()
            self.log("\n=== INCREASED DISK SPACE ===")
            self.check_disk_space()
            
            self.log("\nDisk resize demonstration completed successfully!")
            self.log(f"Don't forget to terminate the instance when done:")
            self.log(f"aws ec2 terminate-instances --instance-ids {self.instance_id} --region {self.region}")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            if self.instance_id:
                self.log(f"You may need to manually terminate instance {self.instance_id}")
            return 1
        
        return 0


if __name__ == "__main__":
    demo = DiskSpaceDemo()
    sys.exit(demo.run_demo())