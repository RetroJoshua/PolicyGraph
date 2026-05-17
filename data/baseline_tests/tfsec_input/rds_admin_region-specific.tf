# PolicyGraph Baseline Test - Terraform Wrapper
# Source: rds_admin_region-specific.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027273+00:00

resource "aws_iam_policy" "rds_admin_region-specific" {
  name        = "rds_admin_region-specific"
  description = "IAM Policy from rds_admin_region-specific.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "rds:*",
      "Resource": [
        "arn:aws:rds:us-east-1:*:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:Describe*"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
})
}
