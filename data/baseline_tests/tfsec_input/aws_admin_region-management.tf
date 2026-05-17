# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_admin_region-management.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.017787+00:00

resource "aws_iam_policy" "aws_admin_region-management" {
  name        = "aws_admin_region-management"
  description = "IAM Policy from aws_admin_region-management.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Deny",
    "Action": "*",
    "Resource": "*",
    "Condition": {
      "NotIpAddress": {
        "aws:SourceIp": [
          "192.0.2.0/24",
          "203.0.113.0/24"
        ]
      }
    }
  }
})
}
