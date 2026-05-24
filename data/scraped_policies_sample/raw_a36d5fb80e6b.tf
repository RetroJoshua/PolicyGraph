resource "aws_iam_role_policy" "gha_oidc_terraform_permissions" {
  name = "gha_oidc_terraform_permissions"
  role = aws_iam_role.gha_oidc_assume_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:*"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:*" # Full S3 access
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "dynamodb:*" # Full DynamoDB access
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "ec2:*" # Full EC2 access
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "ssm:*",            # Full SSM access
          "ssm:GetParameter", # Specifically for SSM Parameter Store access
          "ssm:PutParameter",
          "ssm:DeleteParameter"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "kms:DescribeKey",     # Permission to describe KMS keys
          "kms:Decrypt",         # Permission to decrypt using KMS
          "kms:Encrypt",         # Permission to encrypt using KMS
          "kms:GenerateDataKey", # Permission to generate data keys
          "kms:GetKeyPolicy",
          "kms:GetKeyRotationStatus",
          "kms:ListResourceTags",
          "kms:ListAliases"
        ]
        Effect   = "Allow"
        Resource = "*" # Replace with your actual KMS key ARN if different
      },
      {
        Action = [
          "iam:*",       # Permission to get IAM roles
          "iam:PassRole" # Permission to pass IAM roles
        ]
        Effect   = "Allow"
        Resource = "*" # Replace with your actual role ARN if different
      },
      {
        Action = [
          "iam:GetOpenIDConnectProvider" # Permission to get OIDC provider details
        ]
        Effect   = "Allow"
        Resource = "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com" # Replace with your actual OIDC provider ARN if different
      }
    ]
  })
}