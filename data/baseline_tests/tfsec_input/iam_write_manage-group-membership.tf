# PolicyGraph Baseline Test - Terraform Wrapper
# Source: iam_write_manage-group-membership.json
# Label: vulnerable
# Vulnerability: group_membership_management
# Severity: medium
# Generated: 2026-05-17T08:15:45.024517+00:00

resource "aws_iam_policy" "iam_write_manage-group-membership" {
  name        = "iam_write_manage-group-membership"
  description = "IAM Policy from iam_write_manage-group-membership.json"
  path        = "/"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ViewGroups",
      "Effect": "Allow",
      "Action": [
        "iam:ListGroups",
        "iam:ListUsers",
        "iam:GetUser",
        "iam:ListGroupsForUser"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ViewEditThisGroup",
      "Effect": "Allow",
      "Action": [
        "iam:AddUserToGroup",
        "iam:RemoveUserFromGroup",
        "iam:GetGroup"
      ],
      "Resource": "arn:aws:iam::*:group/MarketingTeam"
    }
  ]
})
}
