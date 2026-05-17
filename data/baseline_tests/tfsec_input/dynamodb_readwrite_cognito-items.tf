# PolicyGraph Baseline Test - Terraform Wrapper
# Source: dynamodb_readwrite_cognito-items.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.021223+00:00

resource "aws_iam_policy" "dynamodb_readwrite_cognito-items" {
  name        = "dynamodb_readwrite_cognito-items"
  description = "IAM Policy from dynamodb_readwrite_cognito-items.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:DeleteItem",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/MyTable"
      ],
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": [
            "${cognito-identity.amazonaws.com:sub}"
          ]
        }
      }
    }
  ]
})
}
