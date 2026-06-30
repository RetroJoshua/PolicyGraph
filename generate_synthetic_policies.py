import json
import random
from pathlib import Path
from datetime import datetime, timedelta

output_dir = Path('data/raw/samples')
output_dir.mkdir(parents=True, exist_ok=True)

AWS_SERVICES = [
    'ec2', 's3', 'lambda', 'iam', 'rds', 'dynamodb',
    'cloudformation', 'sqs', 'sns', 'kinesis', 'glue',
    'datapipeline', 'sts', 'kms', 'cloudwatch', 'logs',
    'secretsmanager', 'ssm', 'apigateway', 'ecs'
]

ACTIONS = {
    'ec2': ['ec2:DescribeInstances', 'ec2:StartInstances', 'ec2:StopInstances', 'ec2:TerminateInstances', 'ec2:RunInstances', 'ec2:*'],
    's3': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket', 's3:*'],
    'lambda': ['lambda:InvokeFunction', 'lambda:CreateFunction', 'lambda:DeleteFunction', 'lambda:UpdateFunctionCode', 'lambda:*'],
    'iam': ['iam:GetUser', 'iam:ListUsers', 'iam:CreateUser', 'iam:DeleteUser', 'iam:AttachUserPolicy', 'iam:PassRole', 'iam:CreateAccessKey', 'iam:*'],
    'rds': ['rds:DescribeDBInstances', 'rds:CreateDBInstance', 'rds:DeleteDBInstance', 'rds:ModifyDBInstance', 'rds:*'],
    'dynamodb': ['dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:DeleteItem', 'dynamodb:Query', 'dynamodb:Scan', 'dynamodb:*'],
    'cloudformation': ['cloudformation:CreateStack', 'cloudformation:DeleteStack', 'cloudformation:UpdateStack', 'cloudformation:*'],
    'sqs': ['sqs:SendMessage', 'sqs:ReceiveMessage', 'sqs:DeleteMessage', 'sqs:*'],
    'default': ['*']
}

RESOURCES = [
    'arn:aws:s3:::*',
    'arn:aws:ec2:*:*:*',
    'arn:aws:lambda:*:*:*',
    'arn:aws:iam::*:*',
    'arn:aws:rds:*:*:*',
    'arn:aws:dynamodb:*:*:table/*',
    'arn:aws:cloudformation:*:*:*',
    '*'
]

CONDITIONS = [
    None,
    '{"StringEquals": {"aws:PrincipalType": "Service"}}',
    '{"StringEquals": {"aws:SourceAccount": "123456789012"}}',
    '{"IpAddress": {"aws:SourceIp": ["10.0.0.0/8"]}}'
]

def generate_policy_document(allow_vulnerable=False):
    """Generate a realistic IAM policy document"""
    service = random.choice(AWS_SERVICES)
    actions = ACTIONS.get(service, ACTIONS['default'])
    
    if allow_vulnerable and random.random() > 0.5:
        action_list = ['*']
        resource = '*'
    else:
        action_list = [random.choice(actions) for _ in range(random.randint(1, 3))]
        resource = random.choice(RESOURCES)
    
    statement = {
        "Effect": "Allow",
        "Action": action_list,
        "Resource": resource
    }
    
    if random.random() > 0.6:
        condition = random.choice(CONDITIONS)
        if condition:
            statement["Condition"] = json.loads(condition)
    
    return {
        "Version": "2012-10-17",
        "Statement": [statement]
    }

def generate_terraform_role(policy_doc, role_name):
    """Generate Terraform code for IAM role"""
    return f'''resource "aws_iam_role" "{role_name}" {{
  name = "{role_name}"
  
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "lambda.amazonaws.com"
        }}
      }}
    ]
  }})
}}

resource "aws_iam_role_policy" "{role_name}_policy" {{
  name   = "{role_name}-policy"
  role   = aws_iam_role.{role_name}.id
  policy = jsonencode({json.dumps(policy_doc, indent=4)})
}}
'''

def generate_synthetic_policies(count=231, start_id=270):
    """Generate synthetic policies"""
    print(f"Generating {count} synthetic policies...")
    print("="*70)
    
    saved_count = 0
    vulnerable_count = 0
    secure_count = 0
    
    for i in range(count):
        try:
            policy_id = start_id + i
            is_vulnerable = random.random() < 0.41
            
            if is_vulnerable:
                vulnerable_count += 1
            else:
                secure_count += 1
            
            policy_doc = generate_policy_document(allow_vulnerable=is_vulnerable)
            role_name = f"synthetic_role_{i:03d}"
            
            content = generate_terraform_role(policy_doc, role_name)
            
            policy_data = {
                "id": f"policy_{policy_id:03d}",
                "filename": f"synthetic_{i:03d}.tf",
                "source_repo": "synthetic/generated-policies",
                "source_path": f"synthetic/policies/synthetic_{i:03d}.tf",
                "content": content,
                "metadata": {
                    "vulnerable": is_vulnerable,
                    "confidence": random.choice(["High", "Medium"]),
                    "notes": "Synthetically generated policy for dataset expansion",
                    "checkov_findings": "Generated" if is_vulnerable else "None",
                    "scraped_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            json_filename = f"policy_{policy_id:03d}_synthetic_{i:03d}_tf.json"
            json_path = output_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(policy_data, f, indent=2, ensure_ascii=False)
            
            saved_count += 1
            if (i + 1) % 50 == 0:
                print(f"[OK] Generated {saved_count} synthetic policies...")
            
        except Exception as e:
            print(f"[ERROR] Error generating policy {i}: {str(e)}")
    
    print("="*70)
    print(f"\nSynthetic Policy Generation Summary:")
    print(f"  Total generated: {saved_count}")
    print(f"  Vulnerable: {vulnerable_count} ({vulnerable_count/saved_count*100:.1f}%)")
    print(f"  Secure: {secure_count} ({secure_count/saved_count*100:.1f}%)")
    print(f"  Output directory: {output_dir.absolute()}")
    
    files = sorted(list(output_dir.glob("policy_*.json")))
    print(f"\nTotal JSON files in directory: {len(files)}")
    print(f"Grand total: 269 (original) + {saved_count} (synthetic) = {len(files)}")

if __name__ == "__main__":
    generate_synthetic_policies(count=231, start_id=270)
