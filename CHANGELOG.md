# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
<!-- Add new changes here as you develop. 
     When releasing, move these to a new version section below. -->

### Planned
- Restore command for creating new RDS instances from snapshots
- EBS volume backup support
- DynamoDB table backup support

## [0.1.0] - 2025-12-01

### Added
- Initial release of sumi
- **Backup command** - Execute backups with parallel execution and status polling
- **Plan command** - Preview resources that will be backed up with Rich UI
- **Validate command** - Validate configuration structure and AWS credentials
- **RDS support** - Backup both RDS instances and Aurora clusters
- **Tag-based discovery** - Find resources using AWS tags with AND/OR logic
- **Parallel execution** - Configurable concurrent snapshot creation
- **Comprehensive error handling** - Error messages for all AWS operations
- **Config-as-code** - YAML-based configuration with version control support
- **Flexible authentication** - Support for both AWS profiles and IAM role assumption
- **60+ test suite** - Unit and integration tests with excellent coverage
- **CI/CD pipeline** - Automated testing, linting, type checking, and security scanning
- **Professional documentation** - Complete README with examples and configuration reference

### Technical
- Built with Typer for CLI framework
- Uses Rich for beautiful terminal output
- Structured logging with structlog
- Type hints throughout codebase with mypy validation
- Security scanning with bandit
- Code quality enforced with Ruff

### Supported AWS Services
- RDS DB Instances
- RDS DB Clusters (Aurora)

### Configuration Features
- Tag filters with AND/OR logic
- Multiple resource groups in single config
- Profile and role-based authentication
- Configurable parallelism

[Unreleased]: https://github.com/obakengdevelops/sumi/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/obakengdevelops/sumi/releases/tag/v0.1.0
