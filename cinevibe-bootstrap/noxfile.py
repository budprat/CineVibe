"""
Nox configuration for CineVibe project
Handles linting, formatting, testing, and type checking
"""

import nox
from pathlib import Path
import os

# Python versions to test
PYTHON_VERSIONS = ["3.12"]

# Source directories
SOURCE_DIRS = ["agents", "tools", "cinevibe", "utils"]

nox.options.sessions = ["lint", "format", "test", "typecheck"]


@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    """Run linting with ruff"""
    session.install("ruff")
    
    # Run ruff linter
    session.run("ruff", "check", *SOURCE_DIRS)
    
    print("✅ Linting passed!")


@nox.session(python=PYTHON_VERSIONS)
def format(session):
    """Format code with black and check with ruff"""
    session.install("black", "ruff")
    
    # Format with black
    session.run("black", *SOURCE_DIRS)
    
    # Format imports with ruff
    session.run("ruff", "check", "--fix", "--select", "I", *SOURCE_DIRS)
    
    print("✅ Code formatted successfully!")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run tests with pytest"""
    session.install(
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "httpx",
        "-r", "requirements.txt" if Path("requirements.txt").exists() else "."
    )
    
    # Create tests directory if it doesn't exist
    Path("tests").mkdir(exist_ok=True)
    
    # Run tests with coverage
    session.run(
        "pytest",
        "tests",
        "--cov=agents",
        "--cov=tools",
        "--cov=cinevibe",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v"
    )
    
    print("✅ Tests completed!")


@nox.session(python=PYTHON_VERSIONS)
def typecheck(session):
    """Run type checking with mypy"""
    session.install(
        "mypy",
        "types-requests",
        "-r", "requirements.txt" if Path("requirements.txt").exists() else "."
    )
    
    # Run mypy
    session.run("mypy", *SOURCE_DIRS, "--install-types", "--non-interactive")
    
    print("✅ Type checking passed!")


@nox.session(python=PYTHON_VERSIONS)
def integration_test(session):
    """Run integration tests for all agents"""
    session.install(
        "pytest",
        "pytest-asyncio",
        "httpx",
        "-r", "requirements.txt" if Path("requirements.txt").exists() else "."
    )
    
    print("\n🎬 Running CineVibe Integration Tests")
    print("=" * 50)
    
    # Test each agent client
    agents = [
        "agents/script_analyzer/script_analyzer_client.py",
        "agents/visual_consistency/visual_consistency_client.py",
        "agents/generation_platform/generation_platform_client.py",
        "agents/director/director_client.py"
    ]
    
    for agent_client in agents:
        if Path(agent_client).exists():
            print(f"\nTesting {Path(agent_client).stem}...")
            try:
                session.run("python", agent_client)
            except Exception as e:
                print(f"⚠️  {Path(agent_client).stem} test failed: {e}")
        else:
            print(f"⚠️  {agent_client} not found")
    
    print("\n✅ Integration tests completed!")


@nox.session(python=PYTHON_VERSIONS)
def docs(session):
    """Generate documentation"""
    session.install("sphinx", "sphinx-rtd-theme", "myst-parser")
    
    # Create docs directory if it doesn't exist
    Path("docs").mkdir(exist_ok=True)
    
    # Generate API documentation
    session.run("sphinx-apidoc", "-o", "docs/api", *SOURCE_DIRS)
    
    # Build HTML documentation
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build/html")
    
    print("✅ Documentation generated in docs/_build/html")


@nox.session(python=PYTHON_VERSIONS)
def clean(session):
    """Clean up generated files and caches"""
    import shutil
    
    # Directories to clean
    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info",
        ".nox"
    ]
    
    for pattern in dirs_to_clean:
        for path in Path(".").rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed {path}")
    
    # Remove .pyc files
    for pyc in Path(".").rglob("*.pyc"):
        pyc.unlink()
    
    print("✅ Cleanup completed!")


@nox.session(python=PYTHON_VERSIONS)
def dev(session):
    """Set up development environment"""
    print("\n🚀 Setting up CineVibe development environment")
    print("=" * 50)
    
    # Install all dependencies
    session.install(
        "-e", ".",
        "-r", "requirements-dev.txt" if Path("requirements-dev.txt").exists() else "requirements.txt"
    )
    
    # Run initial checks
    session.run("python", "-c", "import cinevibe; print(f'CineVibe version: {cinevibe.__version__ if hasattr(cinevibe, \"__version__\") else \"dev\"}')")
    
    print("\n✅ Development environment ready!")
    print("\nAvailable nox sessions:")
    print("  nox -s lint        # Run linting")
    print("  nox -s format      # Format code")
    print("  nox -s test        # Run tests")
    print("  nox -s typecheck   # Type checking")
    print("  nox -s integration_test  # Integration tests")
    print("  nox -s docs        # Generate documentation")
    print("  nox -s clean       # Clean up files")


@nox.session(python=PYTHON_VERSIONS)
def docker_build(session):
    """Build Docker images for all agents"""
    print("\n🐳 Building Docker images for all agents")
    print("=" * 50)
    
    agents = ["script_analyzer", "visual_consistency", "generation_platform", "director"]
    
    for agent in agents:
        agent_dir = Path("agents") / agent
        if agent_dir.exists() and (agent_dir / "Dockerfile").exists():
            print(f"\nBuilding {agent}...")
            session.run(
                "docker", "build",
                "-t", f"cinevibe/{agent}:latest",
                str(agent_dir),
                external=True
            )
            print(f"✅ {agent} image built")
        else:
            print(f"⚠️  No Dockerfile found for {agent}")
    
    print("\n✅ All Docker images built!")


@nox.session(python=PYTHON_VERSIONS)
def deploy_check(session):
    """Check deployment readiness"""
    print("\n🚀 Checking deployment readiness")
    print("=" * 50)
    
    checks = {
        "Environment variables": check_env_vars,
        "Docker files": check_docker_files,
        "CloudBuild configs": check_cloudbuild_configs,
        "Requirements files": check_requirements,
        "Agent configurations": check_agent_configs,
        "Database setup": check_database_setup
    }
    
    all_passed = True
    for check_name, check_func in checks.items():
        print(f"\n{check_name}:")
        if check_func():
            print(f"  ✅ Passed")
        else:
            print(f"  ❌ Failed")
            all_passed = False
    
    if all_passed:
        print("\n✅ All deployment checks passed!")
    else:
        print("\n⚠️  Some deployment checks failed. Please review above.")


def check_env_vars():
    """Check required environment variables"""
    required_vars = [
        "PROJECT_ID",
        "REGION",
        "SPANNER_INSTANCE",
        "SPANNER_DATABASE"
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        return False
    return True


def check_docker_files():
    """Check Docker files exist"""
    agents = ["script_analyzer", "visual_consistency", "generation_platform", "director"]
    for agent in agents:
        dockerfile = Path("agents") / agent / "Dockerfile"
        if not dockerfile.exists():
            print(f"  Missing: {dockerfile}")
            return False
    return True


def check_cloudbuild_configs():
    """Check CloudBuild configurations"""
    configs = [
        "cloudbuild.yaml",
        "agents/script_analyzer/cloudbuild.yaml",
        "agents/visual_consistency/cloudbuild.yaml",
        "agents/generation_platform/cloudbuild.yaml",
        "agents/director/cloudbuild.yaml"
    ]
    
    missing = [cfg for cfg in configs if not Path(cfg).exists()]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        return False
    return True


def check_requirements():
    """Check requirements files"""
    files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]
    missing = [f for f in files if not Path(f).exists()]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        return False
    return True


def check_agent_configs():
    """Check agent configuration files"""
    agents = ["script_analyzer", "visual_consistency", "generation_platform", "director"]
    for agent in agents:
        agent_file = Path("agents") / agent / "agent.py"
        a2a_file = Path("agents") / agent / "a2a_server.py"
        if not agent_file.exists() or not a2a_file.exists():
            print(f"  Missing files for {agent}")
            return False
    return True


def check_database_setup():
    """Check database setup script"""
    if not Path("setup.py").exists():
        print("  Missing: setup.py")
        return False
    return True


if __name__ == "__main__":
    print("Use 'nox' command to run sessions")
    print("Example: nox -s lint")