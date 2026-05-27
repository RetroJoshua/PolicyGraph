data "aws_iam_policy_document" "lambda_start_yolo_task" {
  statement {
    sid       = "RunYoloTask"
    actions   = ["ecs:RunTask"]
    resources = [replace(aws_ecs_task_definition.yolo_detect_worker.arn, "/:[0-9]+$/", ":*")]
  }

  statement {
    sid     = "PassYoloRoles"
    actions = ["iam:PassRole"]
    resources = [
      aws_iam_role.yolo_detect_worker_task.arn,
      aws_iam_role.yolo_detect_worker_execution.arn,
    ]
  }
}