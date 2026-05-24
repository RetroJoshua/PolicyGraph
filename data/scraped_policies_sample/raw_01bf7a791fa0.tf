resource "aws_iam_policy" "karpenter_controller" {
  name   = "karpenter-controller-${local.id}"
  policy = data.aws_iam_policy_document.karpenter_controller.json
}