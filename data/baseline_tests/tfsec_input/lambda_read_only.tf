# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_read_only.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.026919+00:00

resource "aws_iam_policy" "lambda_read_only" {
  name        = "lambda_read_only"
  description = "IAM Policy from lambda_read_only.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:GetPolicy",
        "lambda:ListFunctions",
        "lambda:ListVersionsByFunction",
        "lambda:ListAliases",
        "lambda:ListTags",
        "lambda:GetAccountSettings"
      ],
      "Resource": "*"
    }
  ]
})
}
