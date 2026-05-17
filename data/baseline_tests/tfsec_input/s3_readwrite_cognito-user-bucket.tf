# PolicyGraph Baseline Test - Terraform Wrapper
# Source: s3_readwrite_cognito-user-bucket.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027418+00:00

resource "aws_iam_policy" "s3_readwrite_cognito-user-bucket" {
  name        = "s3_readwrite_cognito-user-bucket"
  description = "IAM Policy from s3_readwrite_cognito-user-bucket.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListYourObjects",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": [
        "arn:aws:s3:::bucket-name"
      ],
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "cognito/application-name/${cognito-identity.amazonaws.com:sub}/*"
          ]
        }
      }
    },
    {
      "Sid": "ReadWriteDeleteYourObjects",
      "Effect": "Allow",
      "Action": [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::bucket-name/cognito/application-name/${cognito-identity.amazonaws.com:sub}/*"
      ]
    }
  ]
})
}
