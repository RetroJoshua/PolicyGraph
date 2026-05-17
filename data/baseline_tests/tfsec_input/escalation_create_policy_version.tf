# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_create_policy_version.json
# Label: vulnerable
# Vulnerability: create_policy_version
# Severity: critical
# Generated: 2026-05-17T08:15:45.023468+00:00

resource "aws_iam_policy" "escalation_create_policy_version" {
  name        = "escalation_create_policy_version"
  description = "IAM Policy from escalation_create_policy_version.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:CreatePolicyVersion",
      "Resource": "arn:aws:iam::*:policy/*"
    }
  ]
})
}
