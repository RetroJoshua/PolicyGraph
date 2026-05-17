# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_layer_management.json
# Label: secure
# Vulnerability: none
# Severity: medium
# Generated: 2026-05-17T08:15:45.025069+00:00

resource "aws_iam_policy" "lambda_layer_management" {
  name        = "lambda_layer_management"
  description = "IAM Policy from lambda_layer_management.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:PublishLayerVersion",
        "lambda:GetLayerVersion",
        "lambda:ListLayers",
        "lambda:ListLayerVersions",
        "lambda:DeleteLayerVersion"
      ],
      "Resource": "*"
    }
  ]
})
}
