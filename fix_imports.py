#!/usr/bin/env python3
import os
import re

base = "/Users/admin/Desktop/work/inkpath/frontend"

def replace_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace relative paths with @/ aliases
    patterns = [
        # app/ → @/components/
        (r'\.\./components/', '@/components/'),
        (r'\.\./\.\./components/', '@/components/'),
        # components/ → @/lib, @/hooks
        (r'\.\./lib/', '@/lib/'),
        (r'\.\./\.\./lib/', '@/lib/'),
        (r'\.\./hooks/', '@/hooks/'),
        (r'\.\./\.\./hooks/', '@/hooks/'),
        # hooks/ → @/lib
        (r'\.\./lib/', '@/lib/'),
    ]
    
    new_content = content
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, new_content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed: {filepath}")

for root, dirs, files in os.walk(base):
    # Skip node_modules and .next
    if 'node_modules' in root or '.next' in root:
        continue
    for f in files:
        if f.endswith(('.tsx', '.ts')):
            filepath = os.path.join(root, f)
            replace_imports(filepath)
