# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_deny_ip-based.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.020536+00:00

resource "aws_iam_policy" "aws_deny_ip-based" {
  name        = "aws_deny_ip-based"
  description = "IAM Policy from aws_deny_ip-based.json"
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
