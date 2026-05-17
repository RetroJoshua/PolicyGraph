# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_vpc_read_only.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028433+00:00

resource "aws_iam_policy" "secure_vpc_read_only" {
  name        = "secure_vpc_read_only"
  description = "IAM Policy from secure_vpc_read_only.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkAcls",
        "ec2:DescribeRouteTables",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeNatGateways"
      ],
      "Resource": "*"
    }
  ]
})
}
