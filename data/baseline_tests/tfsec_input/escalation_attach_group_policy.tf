# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_attach_group_policy.json
# Label: vulnerable
# Vulnerability: attach_group_policy
# Severity: critical
# Generated: 2026-05-17T08:15:45.022538+00:00

resource "aws_iam_policy" "escalation_attach_group_policy" {
  name        = "escalation_attach_group_policy"
  description = "IAM Policy from escalation_attach_group_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:AttachGroupPolicy",
      "Resource": "arn:aws:iam::*:group/*"
    }
  ]
})
}
