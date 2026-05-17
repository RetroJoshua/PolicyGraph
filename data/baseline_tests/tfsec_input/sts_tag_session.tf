# PolicyGraph Baseline Test - Terraform Wrapper
# Source: sts_tag_session.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.029719+00:00

resource "aws_iam_policy" "sts_tag_session" {
  name        = "sts_tag_session"
  description = "IAM Policy from sts_tag_session.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ],
      "Resource": "arn:aws:iam::123456789012:role/TaggedRole",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Project": "MyProject"
        }
      }
    }
  ]
})
}
