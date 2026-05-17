# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_config_remediation_service_role_policy.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.019183+00:00

resource "aws_iam_policy" "aws_config_remediation_service_role_policy" {
  name        = "aws_config_remediation_service_role_policy"
  description = "IAM Policy from aws_config_remediation_service_role_policy.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "ssm:GetDocument",
        "ssm:DescribeDocument",
        "ssm:StartAutomationExecution"
      ],
      "Resource": "*",
      "Effect": "Allow"
    },
    {
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ssm.amazonaws.com"
        }
      },
      "Action": "iam:PassRole",
      "Resource": "*",
      "Effect": "Allow"
    }
  ]
})
}
