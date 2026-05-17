# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_ec2_run.json
# Label: vulnerable
# Vulnerability: passrole_ec2
# Severity: critical
# Generated: 2026-05-17T08:15:45.023668+00:00

resource "aws_iam_policy" "escalation_passrole_ec2_run" {
  name        = "escalation_passrole_ec2_run"
  description = "IAM Policy from escalation_passrole_ec2_run.json"
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
      "Action": "ec2:RunInstances",
      "Resource": "*"
    }
  ]
})
}
