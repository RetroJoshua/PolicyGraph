# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_decode_authorization_message.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028800+00:00

resource "aws_iam_policy" "sts_decode_authorization_message" {
  name        = "sts_decode_authorization_message"
  description = "IAM Policy from sts_decode_authorization_message.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:DecodeAuthorizationMessage",
      "Resource": "*"
    }
  ]
})
}
