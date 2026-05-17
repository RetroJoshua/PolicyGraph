# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_update_assume_role_policy.json
# Label: vulnerable
# Vulnerability: update_assume_role_policy
# Severity: high
# Generated: 2026-05-17T08:15:45.024149+00:00

resource "aws_iam_policy" "escalation_update_assume_role_policy" {
  name        = "escalation_update_assume_role_policy"
  description = "IAM Policy from escalation_update_assume_role_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:UpdateAssumeRolePolicy",
      "Resource": "arn:aws:iam::*:role/*"
    }
  ]
})
}
