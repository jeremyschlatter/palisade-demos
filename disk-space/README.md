# Disk Space Demo

This directory contains scripts that demonstrate disk space management on different platforms:

## Fly.io Disk Space Demo

The `fly-disk-demo.sh` script demonstrates disk space management on Fly.io:

1. Creates a small VM with minimal disk space
2. Checks disk space on the VM
3. Creates and attaches a volume
4. Extends the volume size
5. Verifies the increased disk space

### Prerequisites

- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- Authenticated with Fly.io (`flyctl auth login`)
- jq, grep, sed, awk commands available

### Usage

```bash
./fly-disk-demo.sh [options]
```

### Options

- `--cleanup`: Automatically clean up resources when done
- `--skip-deploy`: Skip deployment if app already exists
- `--skip-volume`: Skip volume creation if it already exists
- `--skip-checks`: Skip prerequisites checks
- `--debug`: Enable verbose debug output
- `--help`: Show this help message

### Examples

Run the full demo, cleaning up at the end:
```bash
./fly-disk-demo.sh --cleanup
```

Skip the deployment step if app already exists:
```bash
./fly-disk-demo.sh --skip-deploy
```

## AWS Disk Demo

The `aws-disk-demo.sh` script demonstrates disk space management on AWS EC2:

- See `aws-key-instructions.md` for key setup instructions
- Refer to the script comments for more details