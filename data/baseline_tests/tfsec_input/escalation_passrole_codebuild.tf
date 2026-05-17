# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_codebuild.json
# Label: vulnerable
# Vulnerability: passrole_codebuild
# Severity: high
# Generated: 2026-05-17T08:15:45.023571+00:00

resource "aws_iam_policy" "escalation_passrole_codebuild" {
  name        = "escalation_passrole_codebuild"
  description = "IAM Policy from escalation_passrole_codebuild.json"
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
        "codebuild:CreateProject",
        "codebuild:StartBuild"
      ],
      "Resource": "*"
    }
  ]
})
}
