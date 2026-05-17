# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_write_passrole-to-service.json
# Label: vulnerable
# Vulnerability: passrole
# Severity: medium
# Generated: 2026-05-17T08:15:45.024570+00:00

resource "aws_iam_policy" "iam_write_passrole-to-service" {
  name        = "iam_write_passrole-to-service"
  description = "IAM Policy from iam_write_passrole-to-service.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "cloudwatch.amazonaws.com"
        }
      }
    }
  ]
})
}
