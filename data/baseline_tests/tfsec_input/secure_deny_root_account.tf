# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_deny_root_account.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027649+00:00

resource "aws_iam_policy" "secure_deny_root_account" {
  name        = "secure_deny_root_account"
  description = "IAM Policy from secure_deny_root_account.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    }
  ]
})
}
