# PolicyGraph Baseline Test - Terraform Wrapper
# Source: aws_conditional_date-range-access.json
# Label: secure
# Vulnerability: none
# Severity: low
# Generated: 2026-05-17T08:15:45.019034+00:00

resource "aws_iam_policy" "aws_conditional_date-range-access" {
  name        = "aws_conditional_date-range-access"
  description = "IAM Policy from aws_conditional_date-range-access.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "service-prefix:action-name",
      "Resource": "*",
      "Condition": {
        "DateGreaterThan": {
          "aws:CurrentTime": "2020-04-01T00:00:00Z"
        },
        "DateLessThan": {
          "aws:CurrentTime": "2020-06-30T23:59:59Z"
        }
      }
    }
  ]
})
}
