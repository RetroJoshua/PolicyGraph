# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_config_multi_account_setup_policy.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.019121+00:00

resource "aws_iam_policy" "aws_config_multi_account_setup_policy" {
  name        = "aws_config_multi_account_setup_policy"
  description = "IAM Policy from aws_config_multi_account_setup_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "config:PutConfigRule",
        "config:DeleteConfigRule"
      ],
      "Resource": "arn:aws:config:*:*:config-rule/aws-service-rule/config-multiaccountsetup.amazonaws.com/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "config:DescribeConfigurationRecorders"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "organizations:ListAccounts",
        "organizations:DescribeOrganization",
        "organizations:ListAWSServiceAccessForOrganization",
        "organizations:DescribeAccount"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "config:PutConformancePack",
        "config:DeleteConformancePack"
      ],
      "Resource": "arn:aws:config:*:*:conformance-pack/aws-service-conformance-pack/config-multiaccountsetup.amazonaws.com/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "config:DescribeConformancePackStatus"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:GetRole"
      ],
      "Resource": "arn:aws:iam::*:role/aws-service-role/config-conforms.amazonaws.com/AWSServiceRoleForConfigConforms"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateServiceLinkedRole"
      ],
      "Resource": "arn:aws:iam::*:role/aws-service-role/config-conforms.amazonaws.com/AWSServiceRoleForConfigConforms",
      "Condition": {
        "StringLike": {
          "iam:AWSServiceName": "config-conforms.amazonaws.com"
        }
      }
    },
    {
      "Action": "iam:PassRole",
      "Resource": "*",
      "Effect": "Allow",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ssm.amazonaws.com"
        }
      }
    }
  ]
})
}
