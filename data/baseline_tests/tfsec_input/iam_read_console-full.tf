# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_read_console-full.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024285+00:00

resource "aws_iam_policy" "iam_read_console-full" {
  name        = "iam_read_console-full"
  description = "IAM Policy from iam_read_console-full.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Action": [
      "iam:Get*",
      "iam:List*",
      "iam:Generate*"
    ],
    "Resource": "*"
  }
})
}
