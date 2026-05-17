# PolicyGraph Baseline Test - Terraform Wrapper
# Source: s3_readwrite_mfa-protected.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027543+00:00

resource "aws_iam_policy" "s3_readwrite_mfa-protected" {
  name        = "s3_readwrite_mfa-protected"
  description = "IAM Policy from s3_readwrite_mfa-protected.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::bucket-name",
        "arn:aws:s3:::bucket-name/*"
      ]
    },
    {
      "Effect": "Deny",
      "NotAction": "s3:*",
      "NotResource": [
        "arn:aws:s3:::bucket-name",
        "arn:aws:s3:::bucket-name/*"
      ]
    }
  ]
})
}
