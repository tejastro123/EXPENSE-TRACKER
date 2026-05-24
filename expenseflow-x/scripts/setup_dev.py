#!/usr/bin/env python3
"""
ExpenseFlow X — Development Setup Script
Sets up the local development environment
"""
import os
import sys
import subprocess
import shutil


def run(cmd: str, cwd: str = ".", exit_on_fail: bool = True):
    """Run shell command"""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        if exit_on_fail:
            print(f"❌ Command failed: {cmd}")
            sys.exit(1)
        else:
            raise RuntimeError(f"Command failed: {cmd}")
    return result


def main():
    print("=" * 60)
    print("🚀 ExpenseFlow X — Development Setup")
    print("=" * 60)

    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    missing_tools = []
    
    # Check core runtimes
    for tool in ["python", "node", "npm"]:
        if not shutil.which(tool):
            print(f"  ❌ {tool} not found")
            missing_tools.append(tool)
        else:
            print(f"  ✅ {tool} found")

    # Check Docker & Compose
    has_docker = shutil.which("docker") is not None
    has_docker_compose_standalone = shutil.which("docker-compose") is not None
    has_docker_compose_v2 = False

    if has_docker:
        print("  ✅ docker found")
        try:
            res = subprocess.run("docker compose version", shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                has_docker_compose_v2 = True
        except Exception:
            pass
    else:
        print("  ❌ docker not found")
        missing_tools.append("docker")

    compose_cmd = None
    if has_docker_compose_standalone:
        print("  ✅ docker-compose found")
        compose_cmd = "docker-compose"
    elif has_docker_compose_v2:
        print("  ✅ docker compose (v2 plugin) found")
        compose_cmd = "docker compose"
    else:
        print("  ❌ docker-compose / docker compose plugin not found")
        missing_tools.append("docker-compose")

    # Exit early only for critical development runtimes
    critical_missing = [t for t in ["python", "node", "npm"] if t in missing_tools]
    if critical_missing:
        print(f"\n❌ Missing critical runtimes: {', '.join(critical_missing)}. Please install them and try again.")
        sys.exit(1)

    # Create .env from example
    print("\n📋 Setting up environment...")
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("  ✅ Created .env from .env.example — please review and update secrets!")
    else:
        print("  ℹ️  .env already exists, skipping")

    # Create placeholder dirs
    print("\n📂 Creating directory structure...")
    dirs = [
        "ml/models/cache",
        "ml/rag/knowledge_base",
        "infrastructure/docker/grafana/dashboards",
        "infrastructure/docker/grafana/datasources",
        "infrastructure/docker/logstash/pipeline",
        "infrastructure/nginx/ssl",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        # Create .gitkeep
        open(os.path.join(d, ".gitkeep"), "w").close()
    print("  ✅ Directories created")

    # Install frontend dependencies
    print("\n📦 Installing frontend dependencies...")
    if os.path.exists("apps/frontend"):
        run("npm install", cwd="apps/frontend")
        print("  ✅ Frontend dependencies installed")

    # Build RAG knowledge base
    print("\n📚 Creating RAG knowledge base...")
    try:
        run("python ml/rag/financial_rag.py", cwd=".", exit_on_fail=False)
        print("  ✅ Knowledge base initialized")
    except Exception:
        print("  ⚠️ RAG setup skipped (Python ML dependencies not installed yet)")

    # Start Docker services
    if compose_cmd:
        print(f"\n🐳 Starting Docker services using '{compose_cmd}'...")
        print("  This may take a few minutes on first run (pulling images)...")
        try:
            run(f"{compose_cmd} up -d postgres redis")
            print("  ✅ Databases started")
            # Wait for DB
            import time
            print("  ⏳ Waiting for PostgreSQL to be ready...")
            time.sleep(10)
        except Exception as e:
            print(f"  ❌ Failed to start docker services: {e}")
    else:
        print("\n🐳 Skipping Docker services setup (docker/docker-compose missing).")
        print("  ⚠️ You will need to start PostgreSQL and Redis manually or install Docker and run:")
        print("     docker compose up -d postgres redis")

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("  1. Update .env with your API keys (OpenAI, Pinecone, etc.)")
    print(f"  2. Start all services: {compose_cmd or 'docker compose'} up")
    print("  3. Start frontend: cd apps/frontend && npm run dev")
    print("  4. Access app at: http://localhost:3000")
    print("\n🔗 Service URLs:")
    print("  Frontend:         http://localhost:3000")
    print("  API Gateway:      http://localhost:8000")
    print("  API Docs:         http://localhost:8000/docs")
    print("  Admin Dashboard:  http://localhost:3001")
    print("  Analytics Portal: http://localhost:8501")
    print("  Grafana:          http://localhost:3030")
    print("  Prometheus:       http://localhost:9090")
    print("  Celery Flower:    http://localhost:5555")
    print("\n💡 Default admin credentials:")
    print("  Email: admin@expenseflowx.com")
    print("  Password: Admin@1234! (CHANGE IMMEDIATELY!)")


if __name__ == "__main__":
    main()
