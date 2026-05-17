# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_create_login_profile.json
# Label: vulnerable
# Vulnerability: create_login_profile
# Severity: critical
# Generated: 2026-05-17T08:15:45.023419+00:00

resource "aws_iam_policy" "escalation_create_login_profile" {
  name        = "escalation_create_login_profile"
  description = "IAM Policy from escalation_create_login_profile.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:CreateLoginProfile",
      "Resource": "arn:aws:iam::*:user/*"
    }
  ]
})
}
