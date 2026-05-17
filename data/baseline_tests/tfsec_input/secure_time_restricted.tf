# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_time_restricted.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028374+00:00

resource "aws_iam_policy" "secure_time_restricted" {
  name        = "secure_time_restricted"
  description = "IAM Policy from secure_time_restricted.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::work-bucket/*",
      "Condition": {
        "DateGreaterThan": {
          "aws:CurrentTime": "2026-01-01T09:00:00Z"
        },
        "DateLessThan": {
          "aws:CurrentTime": "2026-12-31T17:00:00Z"
        }
      }
    }
  ]
})
}
