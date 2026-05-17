# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_sagemaker.json
# Label: vulnerable
# Vulnerability: passrole_sagemaker
# Severity: high
# Generated: 2026-05-17T08:15:45.023862+00:00

resource "aws_iam_policy" "escalation_passrole_sagemaker" {
  name        = "escalation_passrole_sagemaker"
  description = "IAM Policy from escalation_passrole_sagemaker.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateNotebookInstance",
        "sagemaker:CreatePresignedNotebookInstanceUrl"
      ],
      "Resource": "*"
    }
  ]
})
}
