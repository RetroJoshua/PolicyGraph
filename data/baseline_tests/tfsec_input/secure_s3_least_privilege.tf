# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_s3_least_privilege.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028223+00:00

resource "aws_iam_policy" "secure_s3_least_privilege" {
  name        = "secure_s3_least_privilege"
  description = "IAM Policy from secure_s3_least_privilege.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-specific-bucket",
        "arn:aws:s3:::my-specific-bucket/*"
      ]
    }
  ]
})
}
