# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_invoke_specific.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.025017+00:00

resource "aws_iam_policy" "lambda_invoke_specific" {
  name        = "lambda_invoke_specific"
  description = "IAM Policy from lambda_invoke_specific.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:MySpecificFunction"
    }
  ]
})
}
