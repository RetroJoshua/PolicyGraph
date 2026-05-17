# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_put_group_policy.json
# Label: vulnerable
# Vulnerability: put_group_policy
# Severity: critical
# Generated: 2026-05-17T08:15:45.023908+00:00

resource "aws_iam_policy" "escalation_put_group_policy" {
  name        = "escalation_put_group_policy"
  description = "IAM Policy from escalation_put_group_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PutGroupPolicy",
      "Resource": "arn:aws:iam::*:group/*"
    }
  ]
})
}
