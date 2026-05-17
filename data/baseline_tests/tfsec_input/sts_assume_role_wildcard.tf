# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_assume_role_wildcard.json
# Label: vulnerable
# Vulnerability: wildcard_assume_role
# Severity: high
# Generated: 2026-05-17T08:15:45.028679+00:00

resource "aws_iam_policy" "sts_assume_role_wildcard" {
  name        = "sts_assume_role_wildcard"
  description = "IAM Policy from sts_assume_role_wildcard.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "*"
    }
  ]
})
}
