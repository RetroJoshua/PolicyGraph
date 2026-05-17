# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_admin_password-policy.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024241+00:00

resource "aws_iam_policy" "iam_admin_password-policy" {
  name        = "iam_admin_password-policy"
  description = "IAM Policy from iam_admin_password-policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Action": [
      "iam:GetAccountPasswordPolicy",
      "iam:UpdateAccountPasswordPolicy"
    ],
    "Resource": "*"
  }
})
}
