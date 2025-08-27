#!/usr/bin/env python3
"""
ZAIN Hospital Management System Setup Script
This script automates the initial setup of the ZAIN HMS project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import secrets
import string

def print_banner():
    """Print the setup banner"""
    print("=" * 60)
    print("🏥 ZAIN Hospital Management System Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_system_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python
    check_python_version()
    
    # Check pip
    try:
        subprocess.run(['pip', '--version'], check=True, capture_output=True)
        print("✅ pip is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pip is not available")
        sys.exit(1)
    
    # Check git (optional)
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        print("✅ git is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: git is not available (optional)")

def create_virtual_environment():
    """Create and activate virtual environment"""
    print("\n🐍 Setting up virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return str(venv_path)
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created")
        return str(venv_path)
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to create virtual environment")
        sys.exit(1)

def get_pip_command(venv_path):
    """Get the correct pip command for the virtual environment"""
    if os.name == 'nt':  # Windows
        return str(Path(venv_path) / "Scripts" / "pip")
    else:  # Unix/Linux/macOS
        return str(Path(venv_path) / "bin" / "pip")

def get_python_command(venv_path):
    """Get the correct python command for the virtual environment"""
    if os.name == 'nt':  # Windows
        return str(Path(venv_path) / "Scripts" / "python")
    else:  # Unix/Linux/macOS
        return str(Path(venv_path) / "bin" / "python")

def install_dependencies(venv_path):
    """Install project dependencies"""
    print("\n📦 Installing dependencies...")
    
    pip_cmd = get_pip_command(venv_path)
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        print("✅ pip upgraded")
        
        # Install requirements
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed")
        
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to install dependencies")
        print("   Try running: pip install -r requirements.txt")
        sys.exit(1)

def generate_secret_key():
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(50))

def setup_environment_file():
    """Setup environment configuration file"""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    # Generate new secret key
    secret_key = generate_secret_key()
    
    # Read .env file and replace secret key
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace the default secret key
        content = content.replace(
            'SECRET_KEY=django-insecure-change-this-in-production-zain-hms-secret-key-2025',
            f'SECRET_KEY={secret_key}'
        )
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file configured with new secret key")
        
    except FileNotFoundError:
        print("❌ Error: .env file not found")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        'logs',
        'backups',
        'backups/database',
        'backups/media',
        'media',
        'media/uploads',
        'media/patients',
        'media/doctors',
        'staticfiles',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def setup_database(venv_path):
    """Setup database and run migrations"""
    print("\n🗄️  Setting up database...")
    
    python_cmd = get_python_command(venv_path)
    
    try:
        # Create cache table
        subprocess.run([python_cmd, 'manage.py', 'createcachetable'], check=True)
        print("✅ Cache table created")
        
        # Run migrations
        subprocess.run([python_cmd, 'manage.py', 'migrate'], check=True)
        print("✅ Database migrations completed")
        
        # Collect static files
        subprocess.run([python_cmd, 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("✅ Static files collected")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Database setup failed - {e}")
        print("   You may need to run migrations manually:")
        print("   python manage.py migrate")

def create_superuser(venv_path):
    """Create a superuser account"""
    print("\n👤 Creating superuser account...")
    
    python_cmd = get_python_command(venv_path)
    
    print("Please create an admin account:")
    try:
        subprocess.run([python_cmd, 'manage.py', 'createsuperuser'], check=True)
        print("✅ Superuser created")
    except subprocess.CalledProcessError:
        print("⚠️  Superuser creation skipped")
    except KeyboardInterrupt:
        print("\n⚠️  Superuser creation cancelled")

def print_next_steps(venv_path):
    """Print next steps for the user"""
    python_cmd = get_python_command(venv_path)
    
    if os.name == 'nt':  # Windows
        activate_cmd = f"venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        activate_cmd = f"source venv/bin/activate"
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print(f"1. Activate virtual environment: {activate_cmd}")
    print(f"2. Start development server: {python_cmd} manage.py runserver")
    print("3. Open http://127.0.0.1:8000 in your browser")
    print("4. Login with your superuser account")
    print("\n📚 Additional commands:")
    print(f"   • Create backup: {python_cmd} manage.py backup_system")
    print(f"   • Check health: {python_cmd} manage.py system_health")
    print(f"   • Clean logs: {python_cmd} manage.py cleanup_logs")
    print("\n📖 Documentation: See PROJECT_STATUS.md for detailed information")
    print("\n🔧 Configuration: Edit .env file for custom settings")

def main():
    """Main setup function"""
    print_banner()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # Setup steps
        check_system_requirements()
        venv_path = create_virtual_environment()
        install_dependencies(venv_path)
        setup_environment_file()
        create_directories()
        setup_database(venv_path)
        
        # Optional superuser creation
        response = input("\nDo you want to create a superuser account now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_superuser(venv_path)
        
        print_next_steps(venv_path)
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
