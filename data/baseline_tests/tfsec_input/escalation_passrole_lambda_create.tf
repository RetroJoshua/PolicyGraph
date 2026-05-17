# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_lambda_create.json
# Label: vulnerable
# Vulnerability: passrole_lambda_create
# Severity: critical
# Generated: 2026-05-17T08:15:45.023767+00:00

resource "aws_iam_policy" "escalation_passrole_lambda_create" {
  name        = "escalation_passrole_lambda_create"
  description = "IAM Policy from escalation_passrole_lambda_create.json"
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
        "lambda:CreateFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
})
}
