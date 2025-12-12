#!/usr/bin/env python
import sys
import warnings
import os
import docker
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from swe_team.crew import EngineeringTeam

# Load environment variables from .env file
# Look for .env in the swe_team directory (parent of src)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Suppress non-critical warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def check_docker():
    """Verifies that Docker is running before starting the Crew."""
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Docker is running.")
    except Exception:
        print("❌ ERROR: Docker is NOT running.")
        print("Please start Docker Desktop and try again.")
        sys.exit(1)

def run():
    """
    Run the autonomous engineering crew.
    """
    # 1. Pre-flight Checks
    check_docker()
    
    # 2. Setup Workspace - use absolute path to swe_team/output
    # This ensures output files always go to the same place regardless of CWD
    swe_team_dir = Path(__file__).parent.parent.parent  # swe_team/
    output_dir = swe_team_dir / 'output'
    
    # Change to swe_team directory so relative paths in tasks.yaml work correctly
    os.chdir(swe_team_dir)
    print(f"📁 Working directory: {os.getcwd()}")
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created output directory: {output_dir}")

    # 3. Load Project Requirements
    # Requirements are now defined in instructions.py for easy editing
    try:
        from swe_team.instructions import REQUIREMENTS, API_BASE_URL, get_requirements_summary
        requirements = REQUIREMENTS
        print(f"📋 Project: {get_requirements_summary()}")
        print(f"🔗 API Base URL: {API_BASE_URL}")
    except ImportError as e:
        print(f"❌ ERROR: Could not import requirements from instructions.py")
        print(f"   {str(e)}")
        print(f"   Make sure instructions.py exists in swe_team/src/swe_team/")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERROR: Invalid requirements in instructions.py")
        print(f"   {str(e)}")
        print(f"   Please define REQUIREMENTS variable with your project description")
        sys.exit(1)

    inputs = {
        'requirements': requirements,
        'current_date': datetime.now().strftime("%Y-%m-%d"),
        'API_BASE_URL': 'http://localhost:3000'  # Default API base URL for examples
    }

    print(f"\n🚀 Starting Engineering Crew with request:\n{requirements}\n")
    
    # 4. Kickoff
    try:
        result = EngineeringTeam().crew().kickoff(inputs=inputs)
        print("\n\n########################")
        print("## MISSION ACCOMPLISHED ##")
        print("########################\n")
        print("Final Result:")
        print(result)
    except Exception as e:
        print(f"\n❌ MISSION FAILED: {str(e)}")

if __name__ == "__main__":
    run()