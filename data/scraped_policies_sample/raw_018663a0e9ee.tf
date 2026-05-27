data "aws_iam_policy_document" "codebuild" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "ecr:GetAuthorizationToken"
    ]
    effect    = "Allow"
    resources = ["*"]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject"
    ]
    effect    = "Allow"
    resources = ["${local.s3_artifact_bucket_arn}/*"]
  }

  statement {
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    effect    = "Allow"
    resources = ["${var.container_repo_arn}"]
  }

  statement {
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecs:Describe*"
    ]
    effect    = "Allow"
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability"
    ]
    effect    = "Allow"
    resources = ["${var.container_repo_arn}"]
  }
}