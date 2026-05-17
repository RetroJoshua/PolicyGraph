# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_delete_stack.json
# Label: vulnerable
# Vulnerability: stack_deletion
# Severity: medium
# Generated: 2026-05-17T08:15:45.020694+00:00

resource "aws_iam_policy" "cloudformation_delete_stack" {
  name        = "cloudformation_delete_stack"
  description = "IAM Policy from cloudformation_delete_stack.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents"
      ],
      "Resource": "*"
    }
  ]
})
}
