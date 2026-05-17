# PolicyGraph Baseline Test - Terraform Wrapper
# Source: ec2_admin_region-full-access.json
# Label: vulnerable
# Vulnerability: full_service_access
# Severity: medium
# Generated: 2026-05-17T08:15:45.021422+00:00

resource "aws_iam_policy" "ec2_admin_region-full-access" {
  name        = "ec2_admin_region-full-access"
  description = "IAM Policy from ec2_admin_region-full-access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "ec2:*",
      "Resource": "*",
      "Effect": "Allow",
      "Condition": {
        "StringEquals": {
          "ec2:Region": "us-east-2"
        }
      }
    }
  ]
})
}
