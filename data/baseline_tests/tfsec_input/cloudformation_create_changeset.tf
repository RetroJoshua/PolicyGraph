# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_create_changeset.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.020589+00:00

resource "aws_iam_policy" "cloudformation_create_changeset" {
  name        = "cloudformation_create_changeset"
  description = "IAM Policy from cloudformation_create_changeset.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ListChangeSets",
        "cloudformation:ExecuteChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/*"
    }
  ]
})
}
