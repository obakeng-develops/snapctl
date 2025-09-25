## snapctl
`snapctl` is a CLI tool that allows you to setup production-grade backups and disaster recovery in under 5 minutes with one config file. Currently, it only supports AWS RDS. But we're working towards supporting other services within the AWS ecosystem.

### Features
- Automated RDS snapshots: daily/hourly schedules, retention policies.
- One-command backup/restore/failover - spin up a standby or replacement DB fast.
- Config-as-code: version your DR plan in Git alongside your app.
- Data stays in your account: no third-party storage or agents.

### Quick Start
#### Installation
```bash
TODO
```

#### Basic Usage
```yaml
# backup-config.yaml
app: acme

provider:
    name: aws
    region: us-east-1

auth:
    role_arn: arn:aws:iam::123456789012:role/BackupRole

protect:
    - type: rds
      name: production-databases
      discover: "tag:Environment=production AND tag:Backup=required"
      retention: 7d
      schedule: daily@3am
```

You can specify a `profile` instead of the `role_arn` in the `auth` section like this:
```yaml
auth:
    profile: local-development-profile
```

The better approach would be to use an IAM role for production and only use profiles in a local development context to test usage of `snapctl`.

You can also set the `retention` and `schedule` globally for all resources like this:
```yaml
# backup-config.yaml
protect:
    retention: 7d
    schedule: daily@3am
    - type: rds
      name: production-databases
      discover: "tag:Environment=production AND tag:Backup=required"
    - type: ebs
      name: ebs-volumes-production
      discover: "tag:Owner=devops"
```

To run a backups:
```bash
# Test configuration
$ snapctl validate config --config backup-config.yaml

# Execute a backup
$ snapctl run --config backup-config.yaml
```

### Production-Grade by Default:
- Tag-based discovery: Automatically find resources using AWS tags.
- Configuration as Code: Version-controlled backup and disaster recovery policies.
- Minimal IAM footprint: Least-privileged IAM policies.

### Roadmap
- AWS
    - [ ] RDS (in-progress)
    - [ ] Aurora (in-progress)
    - [ ] EBS
    - [ ] EC2
    - [ ] S3
    - [ ] DynamoDB
    - [ ] VPC
    - [ ] Redshift
    - [ ] ElastiCache
    - [ ] DocumentDB
    - [ ] Neptune
    - [ ] Lambda
    - [ ] Route53

- [ ] Multi-cloud support (GCP, Azure, DigitalOcean, Linode)
