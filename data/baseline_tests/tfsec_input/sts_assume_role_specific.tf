# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_assume_role_specific.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028583+00:00

resource "aws_iam_policy" "sts_assume_role_specific" {
  name        = "sts_assume_role_specific"
  description = "IAM Policy from sts_assume_role_specific.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::123456789012:role/MySpecificRole"
    }
  ]
})
}
