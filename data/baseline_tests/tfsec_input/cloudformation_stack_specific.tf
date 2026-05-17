# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_stack_specific.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.020928+00:00

resource "aws_iam_policy" "cloudformation_stack_specific" {
  name        = "cloudformation_stack_specific"
  description = "IAM Policy from cloudformation_stack_specific.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplate",
        "cloudformation:UpdateStack"
      ],
      "Resource": "arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/*"
    }
  ]
})
}
