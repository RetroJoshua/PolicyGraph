# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_basic_execution.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024724+00:00

resource "aws_iam_policy" "lambda_basic_execution" {
  name        = "lambda_basic_execution"
  description = "IAM Policy from lambda_basic_execution.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
})
}
