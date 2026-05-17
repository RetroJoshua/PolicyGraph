# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_require_ssl.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028111+00:00

resource "aws_iam_policy" "secure_require_ssl" {
  name        = "secure_require_ssl"
  description = "IAM Policy from secure_require_ssl.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::secure-bucket",
        "arn:aws:s3:::secure-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
})
}
