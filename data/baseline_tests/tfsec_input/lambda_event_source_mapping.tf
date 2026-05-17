# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_event_source_mapping.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.024914+00:00

resource "aws_iam_policy" "lambda_event_source_mapping" {
  name        = "lambda_event_source_mapping"
  description = "IAM Policy from lambda_event_source_mapping.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateEventSourceMapping",
        "lambda:GetEventSourceMapping",
        "lambda:ListEventSourceMappings",
        "lambda:UpdateEventSourceMapping",
        "lambda:DeleteEventSourceMapping"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "kinesis:DescribeStream",
        "kinesis:GetShardIterator",
        "kinesis:GetRecords",
        "dynamodb:DescribeStream",
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator"
      ],
      "Resource": "*"
    }
  ]
})
}
