# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_get_session_token.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.029662+00:00

resource "aws_iam_policy" "sts_get_session_token" {
  name        = "sts_get_session_token"
  description = "IAM Policy from sts_get_session_token.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:GetSessionToken",
      "Resource": "*"
    }
  ]
})
}
