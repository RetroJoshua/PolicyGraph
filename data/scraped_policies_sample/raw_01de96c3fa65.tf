resource "aws_iam_role" "ssm_client" {
  count    = var.enable_test1_vpc ? 1 : 0
  provider = aws.test1

  name               = "SSMClient"
  assume_role_policy = data.aws_iam_policy_document.ssm_trust_policy.json
}