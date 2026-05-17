# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_code_star_full_access.json
# Label: vulnerable
# Vulnerability: full_service_access
# Severity: medium
# Generated: 2026-05-17T08:15:45.018659+00:00

resource "aws_iam_policy" "aws_code_star_full_access" {
  name        = "aws_code_star_full_access"
  description = "IAM Policy from aws_code_star_full_access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CodeStarEC2",
      "Effect": "Allow",
      "Action": [
        "codestar:*",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "cloud9:DescribeEnvironment*",
        "cloud9:ValidateEnvironmentName"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CodeStarCF",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStack*",
        "cloudformation:ListStacks*",
        "cloudformation:GetTemplateSummary"
      ],
      "Resource": [
        "arn:aws:cloudformation:*:*:stack/awscodestar-*"
      ]
    }
  ]
})
}
