# PolicyGraph Baseline Test - Terraform Wrapper
# Source: ec2_write_tag-owner-instances.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.022435+00:00

resource "aws_iam_policy" "ec2_write_tag-owner-instances" {
  name        = "ec2_write_tag-owner-instances"
  description = "IAM Policy from ec2_write_tag-owner-instances.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Owner": "${aws:username}"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": "ec2:DescribeInstances",
      "Resource": "*"
    }
  ]
})
}
