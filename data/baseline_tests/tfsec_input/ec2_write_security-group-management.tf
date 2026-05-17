# PolicyGraph Baseline Test - Terraform Wrapper
# Source: ec2_write_security-group-management.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.022289+00:00

resource "aws_iam_policy" "ec2_write_security-group-management" {
  name        = "ec2_write_security-group-management"
  description = "IAM Policy from ec2_write_security-group-management.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:ModifySecurityGroupRules",
        "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
        "ec2:UpdateSecurityGroupRuleDescriptionsEgress"
      ],
      "Resource": [
        "arn:aws:ec2:us-east-1:111122223333:security-group/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Department": "Test"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:ModifySecurityGroupRules"
      ],
      "Resource": [
        "arn:aws:ec2:us-east-1:111122223333:security-group-rule/*"
      ]
    }
  ]
})
}
