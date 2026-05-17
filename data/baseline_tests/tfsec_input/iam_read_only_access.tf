# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_read_only_access.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024411+00:00

resource "aws_iam_policy" "iam_read_only_access" {
  name        = "iam_read_only_access"
  description = "IAM Policy from iam_read_only_access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:GenerateCredentialReport",
        "iam:GenerateServiceLastAccessedDetails",
        "iam:Get*",
        "iam:List*",
        "iam:SimulateCustomPolicy",
        "iam:SimulatePrincipalPolicy"
      ],
      "Resource": "*"
    }
  ]
})
}
