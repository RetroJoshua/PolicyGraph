# PolicyGraph Baseline Test - Terraform Wrapper
# Source: dynamodb_readwrite_attribute-level.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.021162+00:00

resource "aws_iam_policy" "dynamodb_readwrite_attribute-level" {
  name        = "dynamodb_readwrite_attribute-level"
  description = "IAM Policy from dynamodb_readwrite_attribute-level.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:BatchGetItem",
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/table-name"
      ],
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:Attributes": [
            "column-name-1",
            "column-name-2",
            "column-name-3"
          ]
        },
        "StringEqualsIfExists": {
          "dynamodb:Select": "SPECIFIC_ATTRIBUTES"
        }
      }
    }
  ]
})
}
