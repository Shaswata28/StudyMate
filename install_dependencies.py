#!/usr/bin/env python3
"""
Dependency Installation Script for StudyMate Project
This script installs all required dependencies for both frontend and backend.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def print_step(message):
    """Print a step message."""
    print(f"[*] {message}")


def print_success(message):
    """Print a success message."""
    print(f"[+] {message}")


def print_error(message):
    """Print an error message."""
    print(f"[-] {message}", file=sys.stderr)


def run_command(command, cwd=None, shell=False):
    """Run a command and return success status."""
    try:
        print_step(f"Running: {' '.join(command) if isinstance(command, list) else command}")
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print_error(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {command[0] if isinstance(command, list) else command}")
        return False


def check_command_exists(command):
    """Check if a command exists in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_python_dependencies():
    """Install Python backend dependencies."""
    print_header("Installing Python Backend Dependencies")
    
    backend_dir = Path("python-backend")
    if not backend_dir.exists():
        print_error("python-backend directory not found!")
        return False
    
    requirements_file = backend_dir / "requirements.txt"
    if not requirements_file.exists():
        print_error("requirements.txt not found in python-backend directory!")
        return False
    
    # Check if Python is available
    python_cmd = "python" if check_command_exists("python") else "python3"
    if not check_command_exists(python_cmd):
        print_error("Python is not installed or not in PATH!")
        print_error("Please install Python 3.8 or higher from https://www.python.org/")
        return False
    
    print_step(f"Using Python command: {python_cmd}")
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print_step("Creating virtual environment...")
        if not run_command([python_cmd, "-m", "venv", "venv"], cwd=backend_dir):
            print_error("Failed to create virtual environment!")
            return False
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")
    
    # Determine the pip command based on OS
    if platform.system() == "Windows":
        pip_cmd = str(venv_dir / "Scripts" / "pip.exe")
    else:
        pip_cmd = str(venv_dir / "bin" / "pip")
    
    # Upgrade pip (optional, continue even if it fails)
    print_step("Upgrading pip...")
    run_command([pip_cmd, "install", "--upgrade", "pip"], cwd=backend_dir)
    # Don't fail if pip upgrade fails, it's not critical
    
    # Install dependencies
    print_step("Installing Python dependencies from requirements.txt...")
    if not run_command([pip_cmd, "install", "-r", "requirements.txt"], cwd=backend_dir):
        print_error("Failed to install Python dependencies!")
        return False
    
    print_success("Python dependencies installed successfully!")
    return True


def install_frontend_dependencies():
    """Install frontend dependencies using pnpm."""
    print_header("Installing Frontend Dependencies")
    
    # Check if pnpm is installed
    if not check_command_exists("pnpm"):
        print_error("pnpm is not installed!")
        print_step("Installing pnpm via npm...")
        
        # Check if npm is available
        if not check_command_exists("npm"):
            print_error("npm is not installed!")
            print_error("Please install Node.js from https://nodejs.org/")
            return False
        
        # Install pnpm globally
        if not run_command(["npm", "install", "-g", "pnpm"]):
            print_error("Failed to install pnpm!")
            return False
        
        print_success("pnpm installed successfully!")
    else:
        print_success("pnpm is already installed")
    
    # Install dependencies
    print_step("Installing frontend dependencies with pnpm...")
    if not run_command(["pnpm", "install"]):
        print_error("Failed to install frontend dependencies!")
        return False
    
    print_success("Frontend dependencies installed successfully!")
    return True


def check_env_files():
    """Check if required .env files exist."""
    print_header("Checking Environment Files")
    
    env_files = [
        (".env.example", ".env"),
        ("python-backend/.env.example", "python-backend/.env")
    ]
    
    for example_file, env_file in env_files:
        example_path = Path(example_file)
        env_path = Path(env_file)
        
        if not env_path.exists() and example_path.exists():
            print_step(f"Creating {env_file} from {example_file}...")
            try:
                env_path.write_text(example_path.read_text())
                print_success(f"Created {env_file}")
                print(f"  [!] Please update {env_file} with your actual configuration values!")
            except Exception as e:
                print_error(f"Failed to create {env_file}: {e}")
        elif env_path.exists():
            print_success(f"{env_file} already exists")
        else:
            print_error(f"Neither {env_file} nor {example_file} found!")


def main():
    """Main installation function."""
    print_header("StudyMate Project - Dependency Installation")
    print("This script will install all required dependencies for the project.")
    
    # Check if we're in the project root
    if not Path("package.json").exists():
        print_error("package.json not found! Please run this script from the project root directory.")
        sys.exit(1)
    
    success = True
    
    # Install Python dependencies
    if not install_python_dependencies():
        success = False
        print_error("Python dependency installation failed!")
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        success = False
        print_error("Frontend dependency installation failed!")
    
    # Check environment files
    check_env_files()
    
    # Final summary
    print_header("Installation Summary")
    
    if success:
        print_success("All dependencies installed successfully!")
        print("\nNext steps:")
        print("  1. Update .env files with your configuration")
        print("  2. Update python-backend/.env with your Supabase and Gemini API keys")
        print("  3. Run 'pnpm dev' to start the development server")
        print("  4. Activate Python virtual environment:")
        if platform.system() == "Windows":
            print("     python-backend\\venv\\Scripts\\activate")
        else:
            print("     source python-backend/venv/bin/activate")
        print("  5. Run Python backend: cd python-backend && uvicorn main:app --reload")
    else:
        print_error("Some installations failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
