# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_update_login_profile.json
# Label: vulnerable
# Vulnerability: update_login_profile
# Severity: high
# Generated: 2026-05-17T08:15:45.024192+00:00

resource "aws_iam_policy" "escalation_update_login_profile" {
  name        = "escalation_update_login_profile"
  description = "IAM Policy from escalation_update_login_profile.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:UpdateLoginProfile",
      "Resource": "arn:aws:iam::*:user/*"
    }
  ]
})
}
