#!/usr/bin/env python3
"""
Microservices Migration Status Check
Verifies that all services are independent of the backend folder
"""
import os
import sys
import importlib.util
import ast
from pathlib import Path

def check_imports_in_file(file_path):
    """Check for backend folder imports in a Python file"""
    backend_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'backend' in alias.name or 'app.' in alias.name:
                        backend_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and ('backend' in node.module or node.module.startswith('app.')):
                    imports = [alias.name for alias in node.names]
                    backend_imports.append(f"from {node.module} import {', '.join(imports)}")
                    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        
    return backend_imports

def check_service_independence(service_path):
    """Check if a service is independent of the backend folder"""
    python_files = []
    
    # Find all Python files in the service
    for root, dirs, files in os.walk(service_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    
    all_backend_imports = []
    
    for py_file in python_files:
        backend_imports = check_imports_in_file(py_file)
        if backend_imports:
            rel_path = os.path.relpath(py_file, service_path)
            all_backend_imports.append((rel_path, backend_imports))
    
    return python_files, all_backend_imports

def main():
    """Main migration status check"""
    print("🔍 Checking SchemaSage Microservices Migration Status...\n")
    
    services_dir = Path("services")
    if not services_dir.exists():
        print("❌ Services directory not found!")
        return 1
    
    services = [
        "schema-detection",
        "ai-chat", 
        "code-generation",
        "project-management",
        "api-gateway"
    ]
    
    all_independent = True
    
    for service in services:
        service_path = services_dir / service
        
        if not service_path.exists():
            print(f"⚠️  {service}: Directory not found")
            continue
            
        print(f"🔎 Checking {service}...")
        python_files, backend_imports = check_service_independence(service_path)
        
        if not python_files:
            print(f"   ⚠️  No Python files found")
            continue
            
        if backend_imports:
            print(f"   ❌ DEPENDENT - Found backend imports:")
            for file, imports in backend_imports:
                print(f"      📁 {file}:")
                for imp in imports:
                    print(f"         - {imp}")
            all_independent = False
        else:
            print(f"   ✅ INDEPENDENT - {len(python_files)} files checked")
    
    print(f"\n{'='*60}")
    
    if all_independent:
        print("🎉 SUCCESS: All microservices are independent!")
        print("✨ The backend folder can be safely removed.")
        return 0
    else:
        print("❌ MIGRATION INCOMPLETE: Some services still depend on backend folder.")
        print("🔧 Please migrate remaining dependencies before removing backend folder.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
