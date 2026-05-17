# PolicyGraph Baseline Test - Terraform Wrapper
# Source: secure_cloudwatch_read_only.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027596+00:00

resource "aws_iam_policy" "secure_cloudwatch_read_only" {
  name        = "secure_cloudwatch_read_only"
  description = "IAM Policy from secure_cloudwatch_read_only.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        "logs:GetLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
})
}
