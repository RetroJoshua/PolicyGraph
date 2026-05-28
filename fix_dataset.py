import re  
from pathlib import Path  
  
dataset_file = Path('policygraph/dataset.py')  
content = dataset_file.read_text(encoding='utf-8')  
  
# Find and replace the buggy line  
old_line = 'label_text = str(entry.get("label", "secure")).lower()'  
new_code = '''# Read the vulnerable boolean field  
            vulnerable = entry.get("vulnerable", False)  
            label_text = "vulnerable" if vulnerable else "secure"'''  
  
if old_line in content:  
    content = content.replace(old_line, new_code)  
    dataset_file.write_text(content, encoding='utf-8')  
    print("✓ Fixed dataset.py")  
else:  
    print("⚠️  Could not find the old line. Checking current state...")  
    # Show what's currently there  
    lines = content.split('\n')  
    for i, line in enumerate(lines):  
        if 'label_text' in line and 'entry.get' in line:  
            print(f"Line {i}: {line}")  
