# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_update_stack.json
# Label: vulnerable
# Vulnerability: stack_modification
# Severity: medium
# Generated: 2026-05-17T08:15:45.021096+00:00

resource "aws_iam_policy" "cloudformation_update_stack" {
  name        = "cloudformation_update_stack"
  description = "IAM Policy from cloudformation_update_stack.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:UpdateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplate"
      ],
      "Resource": "*"
    }
  ]
})
}
