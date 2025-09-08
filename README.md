### Overview
Snapctl is a CLI-tool built to automate disaster recovery. At the moment, it can only back up Aurora/RDS instances.

When using AWS Organisations, `snaptctl` will setup the required key policies, create the necessary IAM roles and IAM policies and then commence backup of an instance in and cross-account. You can also scan resources to verofy dependencies.

`snapctl` can also restore your Aurora/RDS instances. It will setup VPCs, security groups and instances copies needed to test a restore. You can also check out the cost of this before hand.
