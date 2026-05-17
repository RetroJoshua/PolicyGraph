# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_mfa_required.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028005+00:00

resource "aws_iam_policy" "secure_mfa_required" {
  name        = "secure_mfa_required"
  description = "IAM Policy from secure_mfa_required.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        }
      }
    },
    {
      "Effect": "Deny",
      "Action": [
        "iam:*",
        "sts:*"
      ],
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
})
}
