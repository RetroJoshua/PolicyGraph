# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_attach_user_policy.json
# Label: vulnerable
# Vulnerability: attach_user_policy
# Severity: critical
# Generated: 2026-05-17T08:15:45.023238+00:00

resource "aws_iam_policy" "escalation_attach_user_policy" {
  name        = "escalation_attach_user_policy"
  description = "IAM Policy from escalation_attach_user_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:AttachUserPolicy",
      "Resource": "arn:aws:iam::*:user/*"
    }
  ]
})
}
