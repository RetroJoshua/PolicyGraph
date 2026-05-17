# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_assume_role_cross_account.json
# Label: vulnerable
# Vulnerability: cross_account_access
# Severity: medium
# Generated: 2026-05-17T08:15:45.028537+00:00

resource "aws_iam_policy" "sts_assume_role_cross_account" {
  name        = "sts_assume_role_cross_account"
  description = "IAM Policy from sts_assume_role_cross_account.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::987654321098:role/CrossAccountRole"
    }
  ]
})
}
