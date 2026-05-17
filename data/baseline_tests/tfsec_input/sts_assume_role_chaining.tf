# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_assume_role_chaining.json
# Label: vulnerable
# Vulnerability: role_chaining
# Severity: high
# Generated: 2026-05-17T08:15:45.028487+00:00

resource "aws_iam_policy" "sts_assume_role_chaining" {
  name        = "sts_assume_role_chaining"
  description = "IAM Policy from sts_assume_role_chaining.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetSessionToken",
      "Resource": "*"
    }
  ]
})
}
