# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_read_policy-simulator-api.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024460+00:00

resource "aws_iam_policy" "iam_read_policy-simulator-api" {
  name        = "iam_read_policy-simulator-api"
  description = "IAM Policy from iam_read_policy-simulator-api.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "iam:GetContextKeysForCustomPolicy",
        "iam:GetContextKeysForPrincipalPolicy",
        "iam:SimulateCustomPolicy",
        "iam:SimulatePrincipalPolicy"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
})
}
