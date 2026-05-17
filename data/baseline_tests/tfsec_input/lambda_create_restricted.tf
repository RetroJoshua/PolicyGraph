# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_create_restricted.json
# Label: secure
# Vulnerability: none
# Severity: medium
# Generated: 2026-05-17T08:15:45.024791+00:00

resource "aws_iam_policy" "lambda_create_restricted" {
  name        = "lambda_create_restricted"
  description = "IAM Policy from lambda_create_restricted.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:GetFunction",
        "lambda:ListFunctions"
      ],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:dev-*",
      "Condition": {
        "StringEquals": {
          "lambda:FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:dev-*"
        }
      }
    }
  ]
})
}
