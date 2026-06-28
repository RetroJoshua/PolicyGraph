import json

account_path = 'data/examples/account_1_simple_escalation/account.json'
with open(account_path) as f:
    account = json.load(f)

print("=== ACCOUNT_1_SIMPLE_ESCALATION STRUCTURE ===\n")
print(f"Keys: {list(account.keys())}\n")

if 'users' in account:
    print(f"Users ({len(account['users'])}):")
    for user in account['users']:
        print(f"  - {user.get('name', 'unknown')}")

if 'roles' in account:
    print(f"\nRoles ({len(account['roles'])}):")
    for role in account['roles']:
        print(f"  - {role.get('name', 'unknown')}")

if 'policies' in account:
    print(f"\nPolicies ({len(account['policies'])}):")
    for policy in account['policies'][:5]:
        print(f"  - {policy.get('name', 'unknown')}")

if 'attack_paths' in account:
    print(f"\nAttack Paths ({len(account['attack_paths'])}):")
    for path in account['attack_paths']:
        print(f"  - {path.get('name', 'unknown')} ({path.get('severity', 'unknown')})")

print("\n=== FIRST ATTACK PATH DETAILS ===")
if 'attack_paths' in account and len(account['attack_paths']) > 0:
    path = account['attack_paths'][0]
    print(f"Name: {path.get('name')}")
    print(f"Severity: {path.get('severity')}")
    print(f"Steps:")
    for i, step in enumerate(path.get('steps', []), 1):
        print(f"  {i}. {step}")
