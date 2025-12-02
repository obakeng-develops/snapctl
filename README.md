# sumi

[![PyPI version](https://badge.fury.io/py/sumi.svg)](https://pypi.org/project/sumi/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/obakengdevelops/sumi/actions/workflows/ci.yml/badge.svg)](https://github.com/obakengdevelops/sumi/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`sumi` is a CLI tool that allows you to setup production-grade backups and disaster recovery one config file. Currently, it supports AWS RDS instances and Aurora clusters.

## Features

- **Automated RDS snapshots**: Parallel execution with status tracking
- **Tag-based discovery**: Find resources automatically using AWS tags with AND/OR logic
- **Config-as-code**: Version your DR plan in Git alongside your app
- **Data stays in your account**: No third-party storage or agents

## Installation

### From PyPI (Recommended)

```bash
pip install sumi
```

### From Source (Development Version)

```bash
pip install git+https://github.com/obakengdevelops/sumi.git
```

### Using uv

```bash
uv pip install sumi
```

## Quick Start

### 1. Create a Configuration File

```yaml
# backup-config.yaml
app: my-app

provider:
  name: aws
  region: us-east-1

auth:
  profile: my-aws-profile
  # OR use role_arn: arn:aws:iam::123456789012:role/BackupRole

backup:
  resources:
    - type: rds
      name: production-databases
      discover: "tag:Environment=production"
    - type: rds
      name: staging-databases  
      discover: "tag:Environment=staging"
```

### 2. Validate Configuration

```bash
# Validate config structure
sumi validate --config backup-config.yaml

# Validate config AND test AWS credentials
sumi validate --config backup-config.yaml --auth
```

### 3. Preview Resources

```bash
# See what will be backed up (dry-run)
sumi plan --config backup-config.yaml
```

### 4. Execute Backup

```bash
# Run backup with 3 parallel snapshots
sumi backup --config backup-config.yaml --parallel 3
```

## Tag Filter Examples

**Simple tag:**
```yaml
discover: "tag:Environment=production"
```

**AND condition** (all tags must match):
```yaml
discover: "tag:Environment=production AND tag:Backup=required"
```

**OR condition** (any condition can match):
```yaml
discover: "tag:Environment=production OR tag:Critical=yes"
```

**Complex filters:**
```yaml
discover: "tag:Env=prod AND tag:Backup=true OR tag:Critical=yes"
```

## Commands

### validate
Validate your configuration file structure and optionally test AWS credentials.

```bash
sumi validate --config <file>        # Validate config structure
sumi validate --config <file> --auth # Also test AWS credentials
```

### plan
Preview all resources that will be backed up without making any changes.

```bash
sumi plan --config <file>
```

### backup
Execute backups for all configured resources.

```bash
sumi backup --config <file> --parallel 3  # Run 3 backups in parallel
```

## Configuration Reference

### Required Fields

```yaml
app: string                    # Application name
provider:
  name: "aws"                  # Currently only AWS supported
  region: string               # AWS region (e.g., us-east-1)
auth:
  profile: string              # AWS profile name
  # OR
  role_arn: string            # IAM role ARN to assume
backup:
  resources:
    - type: "rds"              # Resource type (currently only rds)
      name: string             # Friendly name for this resource group
      discover: string         # Tag filter for resource discovery
```

### Tag Filter Syntax

- Single tag: `tag:Key=Value`
- AND operator: `tag:Key1=Value1 AND tag:Key2=Value2`
- OR operator: `tag:Key1=Value1 OR tag:Key2=Value2`
- Combined: `tag:K1=V1 AND tag:K2=V2 OR tag:K3=V3`

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/obakengdevelops/sumi.git
cd sumi

# Install with uv
uv sync

# Install in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cli --cov-report=html

# Run specific test file
pytest cli/tests/unit/test_config.py -v
```

### Code Quality

```bash
# Lint code
ruff check

# Format code
ruff format

# Type check
mypy cli/

# Security scan
bandit -r cli/ -ll
```

## Requirements

- Python >= 3.13
- AWS credentials configured (via `aws configure` or IAM role)
- IAM permissions for:
  - `rds:DescribeDBInstances`
  - `rds:DescribeDBClusters`
  - `rds:CreateDBClusterSnapshot`
  - `rds:DescribeDBClusterSnapshots`
  - `rds:ListTagsForResource`

## Roadmap

- [x] RDS Instances
- [x] Aurora Clusters  
- [x] Tag-based discovery with AND/OR logic
- [x] Parallel backup execution
- [x] CI/CD pipeline with tests
- [ ] Restore command
- [ ] EBS volumes
- [ ] DynamoDB tables
- [ ] S3 bucket versioning
- [ ] Multi-region support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
