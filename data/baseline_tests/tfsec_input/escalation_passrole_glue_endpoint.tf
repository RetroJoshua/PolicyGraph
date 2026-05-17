# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_glue_endpoint.json
# Label: vulnerable
# Vulnerability: passrole_glue
# Severity: high
# Generated: 2026-05-17T08:15:45.023717+00:00

resource "aws_iam_policy" "escalation_passrole_glue_endpoint" {
  name        = "escalation_passrole_glue_endpoint"
  description = "IAM Policy from escalation_passrole_glue_endpoint.json"
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
        "glue:CreateDevEndpoint",
        "glue:GetDevEndpoint",
        "glue:GetDevEndpoints"
      ],
      "Resource": "*"
    }
  ]
})
}
