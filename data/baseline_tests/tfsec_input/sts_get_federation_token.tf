# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_get_federation_token.json
# Label: vulnerable
# Vulnerability: federation_token
# Severity: medium
# Generated: 2026-05-17T08:15:45.028903+00:00

resource "aws_iam_policy" "sts_get_federation_token" {
  name        = "sts_get_federation_token"
  description = "IAM Policy from sts_get_federation_token.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:GetFederationToken",
      "Resource": "*"
    }
  ]
})
}
