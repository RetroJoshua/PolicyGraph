# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_create_access_key.json
# Label: vulnerable
# Vulnerability: create_access_key
# Severity: critical
# Generated: 2026-05-17T08:15:45.023291+00:00

resource "aws_iam_policy" "escalation_create_access_key" {
  name        = "escalation_create_access_key"
  description = "IAM Policy from escalation_create_access_key.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:CreateAccessKey",
      "Resource": "arn:aws:iam::*:user/*"
    }
  ]
})
}
