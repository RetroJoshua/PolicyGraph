resource "aws_iam_role" "default" {
  count = var.enabled && var.external_cluster == false ? 1 : 0

  name                 = module.labels.id
  assume_role_policy   = data.aws_iam_policy_document.assume_role[0].json
  permissions_boundary = var.permissions_boundary

  tags = module.labels.tags
}