# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_read_only.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.020875+00:00

resource "aws_iam_policy" "cloudformation_read_only" {
  name        = "cloudformation_read_only"
  description = "IAM Policy from cloudformation_read_only.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:GetTemplate",
        "cloudformation:ListStacks",
        "cloudformation:ListStackResources"
      ],
      "Resource": "*"
    }
  ]
})
}
