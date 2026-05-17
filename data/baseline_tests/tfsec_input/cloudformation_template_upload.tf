# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_template_upload.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.021046+00:00

resource "aws_iam_policy" "cloudformation_template_upload" {
  name        = "cloudformation_template_upload"
  description = "IAM Policy from cloudformation_template_upload.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate",
        "cloudformation:EstimateTemplateCost",
        "cloudformation:GetTemplateSummary"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cf-templates-bucket/*"
    }
  ]
})
}
