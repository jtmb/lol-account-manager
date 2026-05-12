"""Setup script for development installation"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error: {description} failed!")
        return False
    return True


def main():
    print("League of Legends Account Manager - Setup")
    print("=" * 50)
    
    # Create virtual environment
    if not Path("venv").exists():
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    
    # Activate and install dependencies
    activate_cmd = "venv\\Scripts\\activate.bat" if sys.platform == "win32" else "source venv/bin/activate"
    pip_cmd = f"{activate_cmd} && pip install -r requirements.txt" if sys.platform != "win32" else "venv\\Scripts\\pip install -r requirements.txt"
    
    if not run_command(pip_cmd, "Installing dependencies"):
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nTo run the application:")
    if sys.platform == "win32":
        print("  run.bat")
    else:
        print("  source venv/bin/activate")
        print("  python src/main.py")


if __name__ == "__main__":
    main()
