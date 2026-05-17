# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_lambda_update.json
# Label: vulnerable
# Vulnerability: passrole_lambda_update
# Severity: critical
# Generated: 2026-05-17T08:15:45.023815+00:00

resource "aws_iam_policy" "escalation_passrole_lambda_update" {
  name        = "escalation_passrole_lambda_update"
  description = "IAM Policy from escalation_passrole_lambda_update.json"
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
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
})
}
