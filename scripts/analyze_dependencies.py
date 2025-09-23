#!/usr/bin/env python3
"""
Script to analyze all Python imports in the ZAIN HMS project
and generate a comprehensive dependency report.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
import ast

def extract_imports_from_file(file_path):
    """Extract all imports from a Python file using AST parsing."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Parse the file using AST
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        # Fallback to regex parsing
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extract import statements with regex
            import_pattern = r'^(?:from\s+(\S+)\s+import|import\s+(\S+)).*'
            for line in content.splitlines():
                match = re.match(import_pattern, line.strip())
                if match:
                    module = match.group(1) or match.group(2)
                    if module:
                        imports.add(module.split('.')[0])
        except Exception as fallback_e:
            print(f"Fallback parsing also failed for {file_path}: {fallback_e}")
    
    return imports

def analyze_project_dependencies(project_root):
    """Analyze all Python files in the project for dependencies."""
    project_path = Path(project_root)
    all_imports = defaultdict(list)
    file_count = 0
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_path):
        # Skip certain directories
        skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env', 'staticfiles', 'media'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to analyze...")
    
    for file_path in python_files:
        file_count += 1
        relative_path = os.path.relpath(file_path, project_path)
        imports = extract_imports_from_file(file_path)
        
        for imp in imports:
            all_imports[imp].append(relative_path)
    
    return all_imports, file_count

def categorize_imports(imports_dict):
    """Categorize imports into standard library, third-party, and local."""
    
    # Common standard library modules
    stdlib_modules = {
        'os', 'sys', 'json', 'datetime', 'time', 'logging', 'subprocess', 
        'pathlib', 'secrets', 'hashlib', 're', 'urllib', 'collections',
        'functools', 'itertools', 'operator', 'typing', 'decimal',
        'uuid', 'copy', 'pickle', 'csv', 'xml', 'html', 'http',
        'email', 'base64', 'binascii', 'struct', 'socket', 'ssl',
        'threading', 'multiprocessing', 'asyncio', 'concurrent',
        'math', 'random', 'statistics', 'locale', 'calendar',
        'io', 'tempfile', 'shutil', 'glob', 'fnmatch', 'platform'
    }
    
    # Known third-party packages
    known_third_party = {
        'django', 'rest_framework', 'celery', 'redis', 'requests',
        'pillow', 'pil', 'numpy', 'pandas', 'matplotlib', 'seaborn',
        'reportlab', 'openpyxl', 'xlsxwriter', 'pytz', 'channels',
        'channels_redis', 'daphne', 'whitenoise', 'gunicorn',
        'psycopg2', 'mysql', 'pymongo', 'sqlalchemy', 'alembic',
        'flask', 'fastapi', 'pydantic', 'marshmallow', 'wtforms',
        'jinja2', 'cryptography', 'jwt', 'oauth2', 'social',
        'stripe', 'paypal', 'twilio', 'sendgrid', 'boto3', 'aws',
        'google', 'firebase', 'sentry_sdk', 'newrelic', 'datadog',
        'pytest', 'unittest', 'nose', 'coverage', 'tox', 'black',
        'flake8', 'pylint', 'mypy', 'isort', 'pre_commit',
        'fabric', 'invoke', 'click', 'typer', 'rich', 'colorama',
        'tqdm', 'progressbar', 'schedule', 'crontab', 'apscheduler',
        'scrapy', 'beautifulsoup4', 'lxml', 'selenium', 'playwright',
        'environ', 'python_decouple', 'configparser', 'pyyaml',
        'toml', 'jsonschema', 'cerberus', 'voluptuous', 'schema'
    }
    
    stdlib = {}
    third_party = {}
    local = {}
    
    for module, files in imports_dict.items():
        if module.startswith('apps.') or module.startswith('zain_hms'):
            local[module] = files
        elif module in stdlib_modules:
            stdlib[module] = files
        elif module in known_third_party:
            third_party[module] = files
        else:
            # Check if it might be third-party by common patterns
            if any(pattern in module for pattern in ['django', 'rest_framework', 'celery']):
                third_party[module] = files
            elif module.startswith('_'):  # Private modules, likely stdlib
                stdlib[module] = files
            else:
                third_party[module] = files  # Assume third-party if unknown
    
    return stdlib, third_party, local

def main():
    project_root = "/home/mehedi/Projects/zain_hms"
    
    print("🔍 Analyzing ZAIN HMS Python Dependencies...")
    print("=" * 60)
    
    # Analyze dependencies
    all_imports, file_count = analyze_project_dependencies(project_root)
    
    # Categorize imports
    stdlib, third_party, local = categorize_imports(all_imports)
    
    print(f"\n📊 Analysis Complete!")
    print(f"Files analyzed: {file_count}")
    print(f"Total unique imports: {len(all_imports)}")
    print(f"Standard library modules: {len(stdlib)}")
    print(f"Third-party packages: {len(third_party)}")
    print(f"Local modules: {len(local)}")
    
    print("\n🏗️  STANDARD LIBRARY MODULES:")
    print("-" * 40)
    for module in sorted(stdlib.keys()):
        print(f"  ✓ {module} (used in {len(stdlib[module])} files)")
    
    print("\n📦 THIRD-PARTY PACKAGES:")
    print("-" * 40)
    for module in sorted(third_party.keys()):
        print(f"  📦 {module} (used in {len(third_party[module])} files)")
    
    print("\n🏠 LOCAL MODULES:")
    print("-" * 40)
    for module in sorted(local.keys()):
        print(f"  🏠 {module} (used in {len(local[module])} files)")
    
    # Generate third-party package list for requirements analysis
    print(f"\n📋 THIRD-PARTY PACKAGES FOR REQUIREMENTS.TXT ANALYSIS:")
    print("-" * 60)
    for module in sorted(third_party.keys()):
        print(module)
    
    return third_party

if __name__ == "__main__":
    main()