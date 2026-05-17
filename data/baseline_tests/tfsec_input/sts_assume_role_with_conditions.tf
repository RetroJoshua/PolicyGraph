# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_assume_role_with_conditions.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028733+00:00

resource "aws_iam_policy" "sts_assume_role_with_conditions" {
  name        = "sts_assume_role_with_conditions"
  description = "IAM Policy from sts_assume_role_with_conditions.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::123456789012:role/ConditionedRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "UniqueExternalId123"
        },
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
})
}
