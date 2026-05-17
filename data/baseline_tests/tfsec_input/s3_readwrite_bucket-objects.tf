# PolicyGraph Baseline Test - Terraform Wrapper
# Source: s3_readwrite_bucket-objects.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027346+00:00

resource "aws_iam_policy" "s3_readwrite_bucket-objects" {
  name        = "s3_readwrite_bucket-objects"
  description = "IAM Policy from s3_readwrite_bucket-objects.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListObjectsInBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::bucket-name"
      ]
    },
    {
      "Sid": "AllObjectActions",
      "Effect": "Allow",
      "Action": "s3:*Object",
      "Resource": [
        "arn:aws:s3:::bucket-name/*"
      ]
    }
  ]
})
}
