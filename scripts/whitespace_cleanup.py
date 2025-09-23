#!/usr/bin/env python3
"""
ZAIN HMS Whitespace Cleanup Script
Cleans up blank space issues across CSS, JS, and HTML template files
"""

import os
import re
import glob
from pathlib import Path

class WhitespaceCleanup:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.stats = {
            'files_processed': 0,
            'issues_fixed': 0,
            'css_files': 0,
            'js_files': 0,
            'html_files': 0
        }
    
    def clean_leading_blank_lines(self, content):
        """Remove leading blank lines from content"""
        lines = content.split('\n')
        # Find first non-empty line
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip():
                start_index = i
                break
        
        if start_index > 0:
            self.stats['issues_fixed'] += 1
            return '\n'.join(lines[start_index:])
        return content
    
    def clean_excessive_blank_lines(self, content):
        """Reduce consecutive blank lines to maximum of 2"""
        # Replace 3+ consecutive blank lines with 2
        pattern = r'\n\s*\n\s*\n(\s*\n)+'
        replacement = '\n\n'
        cleaned = re.sub(pattern, replacement, content)
        
        if cleaned != content:
            self.stats['issues_fixed'] += 1
        return cleaned
    
    def standardize_indentation(self, content, file_type):
        """Standardize indentation based on file type"""
        if file_type == 'css':
            # Convert tabs to 4 spaces, fix inconsistent spacing
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Replace tabs with 4 spaces
                line = line.replace('\t', '    ')
                # Fix common CSS indentation issues
                if '{' in line and not line.strip().startswith('/*'):
                    line = re.sub(r'^\s*', '', line)  # Remove leading whitespace for selectors
                elif line.strip() and not line.strip().startswith('}') and '{' not in line:
                    # Property lines should have 4 spaces
                    stripped = line.strip()
                    if stripped and not stripped.startswith('/*') and not stripped.startswith('*'):
                        line = '    ' + stripped
                cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        elif file_type == 'js':
            # Convert tabs to 4 spaces
            content = content.replace('\t', '    ')
            return content
        
        return content
    
    def clean_file(self, file_path):
        """Clean a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_ext = file_path.suffix.lower()
            
            # Determine file type
            if file_ext == '.css':
                file_type = 'css'
                self.stats['css_files'] += 1
            elif file_ext == '.js':
                file_type = 'js'
                self.stats['js_files'] += 1
            elif file_ext == '.html':
                file_type = 'html'
                self.stats['html_files'] += 1
            else:
                return False
            
            # Apply cleanups
            content = self.clean_leading_blank_lines(content)
            content = self.clean_excessive_blank_lines(content)
            
            if file_type in ['css', 'js']:
                content = self.standardize_indentation(content, file_type)
            
            # Remove trailing whitespace from all lines
            lines = content.split('\n')
            lines = [line.rstrip() for line in lines]
            content = '\n'.join(lines)
            
            # Remove trailing blank lines
            content = content.rstrip('\n') + '\n'
            
            # Write back if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Cleaned: {file_path}")
                return True
            else:
                print(f"- No changes: {file_path}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            return False
    
    def clean_css_files(self):
        """Clean all CSS files"""
        print("\n🎨 Cleaning CSS files...")
        css_patterns = [
            str(self.project_root / "static" / "css" / "**" / "*.css"),
            str(self.project_root / "staticfiles" / "css" / "**" / "*.css")
        ]
        
        for pattern in css_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                file_path = Path(file_path)
                self.stats['files_processed'] += 1
                self.clean_file(file_path)
    
    def clean_js_files(self):
        """Clean all JavaScript files"""
        print("\n⚡ Cleaning JavaScript files...")
        js_patterns = [
            str(self.project_root / "static" / "js" / "**" / "*.js"),
            str(self.project_root / "staticfiles" / "js" / "**" / "*.js")
        ]
        
        for pattern in js_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                file_path = Path(file_path)
                # Skip minified files
                if '.min.js' not in str(file_path):
                    self.stats['files_processed'] += 1
                    self.clean_file(file_path)
    
    def clean_template_files(self):
        """Clean template HTML files"""
        print("\n🌐 Cleaning template files...")
        template_patterns = [
            str(self.project_root / "templates" / "**" / "*.html")
        ]
        
        for pattern in template_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                file_path = Path(file_path)
                self.stats['files_processed'] += 1
                self.clean_file(file_path)
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🚀 Starting ZAIN HMS Whitespace Cleanup")
        print(f"📁 Project root: {self.project_root}")
        
        self.clean_css_files()
        self.clean_js_files()
        self.clean_template_files()
        
        print(f"\n📊 Cleanup Statistics:")
        print(f"   Files processed: {self.stats['files_processed']}")
        print(f"   Issues fixed: {self.stats['issues_fixed']}")
        print(f"   CSS files: {self.stats['css_files']}")
        print(f"   JS files: {self.stats['js_files']}")
        print(f"   HTML files: {self.stats['html_files']}")
        print("\n✅ Whitespace cleanup completed!")

def main():
    """Main function"""
    # Get project root (current directory)
    project_root = os.getcwd()
    
    # Run cleanup
    cleaner = WhitespaceCleanup(project_root)
    cleaner.run_cleanup()

if __name__ == "__main__":
    main()