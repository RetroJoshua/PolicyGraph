# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_stacksets_admin.json
# Label: vulnerable
# Vulnerability: stackset_admin
# Severity: high
# Generated: 2026-05-17T08:15:45.020984+00:00

resource "aws_iam_policy" "cloudformation_stacksets_admin" {
  name        = "cloudformation_stacksets_admin"
  description = "IAM Policy from cloudformation_stacksets_admin.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "cloudformation:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/AWSCloudFormationStackSetAdministrationRole"
    },
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/AWSCloudFormationStackSetExecutionRole"
    }
  ]
})
}
