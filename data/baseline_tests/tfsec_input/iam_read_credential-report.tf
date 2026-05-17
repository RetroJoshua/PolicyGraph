# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_read_credential-report.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024351+00:00

resource "aws_iam_policy" "iam_read_credential-report" {
  name        = "iam_read_credential-report"
  description = "IAM Policy from iam_read_credential-report.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Action": [
      "iam:GenerateCredentialReport",
      "iam:GetCredentialReport"
    ],
    "Resource": "*"
  }
})
}
