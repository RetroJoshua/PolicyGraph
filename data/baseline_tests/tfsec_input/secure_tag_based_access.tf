# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_tag_based_access.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.028275+00:00

resource "aws_iam_policy" "secure_tag_based_access" {
  name        = "secure_tag_based_access"
  description = "IAM Policy from secure_tag_based_access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:ResourceTag/Environment": "development",
          "aws:PrincipalTag/Department": "${ec2:ResourceTag/Department}"
        }
      }
    }
  ]
})
}
