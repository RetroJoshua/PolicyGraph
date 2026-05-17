# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_cloudformation.json
# Label: vulnerable
# Vulnerability: passrole_cloudformation
# Severity: critical
# Generated: 2026-05-17T08:15:45.023520+00:00

resource "aws_iam_policy" "escalation_passrole_cloudformation" {
  name        = "escalation_passrole_cloudformation"
  description = "IAM Policy from escalation_passrole_cloudformation.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudformation:*",
      "Resource": "*"
    }
  ]
})
}
