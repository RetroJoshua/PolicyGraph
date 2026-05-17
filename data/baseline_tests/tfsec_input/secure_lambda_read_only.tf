# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_lambda_read_only.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027939+00:00

resource "aws_iam_policy" "secure_lambda_read_only" {
  name        = "secure_lambda_read_only"
  description = "IAM Policy from secure_lambda_read_only.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:GetPolicy",
        "lambda:ListVersionsByFunction",
        "lambda:ListAliases",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "*"
    }
  ]
})
}
