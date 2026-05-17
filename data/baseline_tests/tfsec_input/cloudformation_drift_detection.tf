# PolicyGraph Baseline Test - Terraform Wrapper
# Source: cloudformation_drift_detection.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.020745+00:00

resource "aws_iam_policy" "cloudformation_drift_detection" {
  name        = "cloudformation_drift_detection"
  description = "IAM Policy from cloudformation_drift_detection.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DetectStackDrift",
        "cloudformation:DetectStackResourceDrift",
        "cloudformation:DescribeStackDriftDetectionStatus",
        "cloudformation:DescribeStackResourceDrifts"
      ],
      "Resource": "*"
    }
  ]
})
}
