# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_full_access.json
# Label: vulnerable
# Vulnerability: full_service_access
# Severity: high
# Generated: 2026-05-17T08:15:45.020818+00:00

resource "aws_iam_policy" "cloudformation_full_access" {
  name        = "cloudformation_full_access"
  description = "IAM Policy from cloudformation_full_access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "cloudformation:*",
      "Resource": "*"
    }
  ]
})
}
