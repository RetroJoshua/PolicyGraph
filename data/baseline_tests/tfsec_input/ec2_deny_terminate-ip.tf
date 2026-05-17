# PolicyGraph Baseline Test - Terraform Wrapper
# Source: ec2_deny_terminate-ip.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.021489+00:00

resource "aws_iam_policy" "ec2_deny_terminate-ip" {
  name        = "ec2_deny_terminate-ip"
  description = "IAM Policy from ec2_deny_terminate-ip.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:TerminateInstances"
      ],
      "Resource": [
        "*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": [
        "ec2:TerminateInstances"
      ],
      "Condition": {
        "NotIpAddress": {
          "aws:SourceIp": [
            "192.0.2.0/24",
            "203.0.113.0/24"
          ]
        }
      },
      "Resource": [
        "*"
      ]
    }
  ]
})
}
