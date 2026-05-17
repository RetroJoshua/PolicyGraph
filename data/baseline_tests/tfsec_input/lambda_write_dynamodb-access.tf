# PolicyGraph Baseline Test - Terraform Wrapper
# Source: lambda_write_dynamodb-access.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.027216+00:00

resource "aws_iam_policy" "lambda_write_dynamodb-access" {
  name        = "lambda_write_dynamodb-access"
  description = "IAM Policy from lambda_write_dynamodb-access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadWriteTable",
      "Effect": "Allow",
      "Action": [
        "dynamodb:BatchGetItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/SampleTable"
    },
    {
      "Sid": "GetStreamRecords",
      "Effect": "Allow",
      "Action": "dynamodb:GetRecords",
      "Resource": "arn:aws:dynamodb:*:*:table/SampleTable/stream/* "
    },
    {
      "Sid": "WriteLogStreamsAndGroups",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CreateLogGroup",
      "Effect": "Allow",
      "Action": "logs:CreateLogGroup",
      "Resource": "*"
    }
  ]
})
}
