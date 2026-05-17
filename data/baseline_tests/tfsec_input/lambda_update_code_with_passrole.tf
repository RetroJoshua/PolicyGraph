# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_update_code_with_passrole.json
# Label: vulnerable
# Vulnerability: passrole_lambda_update
# Severity: critical
# Generated: 2026-05-17T08:15:45.026980+00:00

resource "aws_iam_policy" "lambda_update_code_with_passrole" {
  name        = "lambda_update_code_with_passrole"
  description = "IAM Policy from lambda_update_code_with_passrole.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
})
}
