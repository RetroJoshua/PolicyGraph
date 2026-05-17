# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_create_with_passrole.json
# Label: vulnerable
# Vulnerability: passrole_cloudformation
# Severity: critical
# Generated: 2026-05-17T08:15:45.020643+00:00

resource "aws_iam_policy" "cloudformation_create_with_passrole" {
  name        = "cloudformation_create_with_passrole"
  description = "IAM Policy from cloudformation_create_with_passrole.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "cloudformation:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    }
  ]
})
}
