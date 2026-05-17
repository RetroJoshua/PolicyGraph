# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_add_user_to_group.json
# Label: vulnerable
# Vulnerability: add_user_to_group
# Severity: high
# Generated: 2026-05-17T08:15:45.022485+00:00

resource "aws_iam_policy" "escalation_add_user_to_group" {
  name        = "escalation_add_user_to_group"
  description = "IAM Policy from escalation_add_user_to_group.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:AddUserToGroup",
      "Resource": "arn:aws:iam::*:group/*"
    }
  ]
})
}
