# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_get_caller_identity.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028855+00:00

resource "aws_iam_policy" "sts_get_caller_identity" {
  name        = "sts_get_caller_identity"
  description = "IAM Policy from sts_get_caller_identity.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
})
}
