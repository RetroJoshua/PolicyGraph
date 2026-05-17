# PolicyGraph Baseline Test - Terraform Wrapper
# Source: escalation_passrole_datapipeline.json
# Label: vulnerable
# Vulnerability: passrole_datapipeline
# Severity: high
# Generated: 2026-05-17T08:15:45.023620+00:00

resource "aws_iam_policy" "escalation_passrole_datapipeline" {
  name        = "escalation_passrole_datapipeline"
  description = "IAM Policy from escalation_passrole_datapipeline.json"
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
        "datapipeline:CreatePipeline",
        "datapipeline:PutPipelineDefinition",
        "datapipeline:ActivatePipeline"
      ],
      "Resource": "*"
    }
  ]
})
}
