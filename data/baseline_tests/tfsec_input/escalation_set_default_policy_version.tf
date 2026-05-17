# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_set_default_policy_version.json
# Label: vulnerable
# Vulnerability: set_default_policy_version
# Severity: critical
# Generated: 2026-05-17T08:15:45.024104+00:00

resource "aws_iam_policy" "escalation_set_default_policy_version" {
  name        = "escalation_set_default_policy_version"
  description = "IAM Policy from escalation_set_default_policy_version.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion"
      ],
      "Resource": "arn:aws:iam::*:policy/*"
    }
  ]
})
}
