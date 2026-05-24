#!/usr/bin/env python3
"""
ExpenseFlow X — Development Setup Script
Sets up the local development environment
"""
import os
import sys
import subprocess
import shutil


def run(cmd: str, cwd: str = "."):
    """Run shell command"""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("🚀 ExpenseFlow X — Development Setup")
    print("=" * 60)

    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    for tool in ["docker", "docker-compose", "python", "node", "npm"]:
        if not shutil.which(tool):
            print(f"  ❌ {tool} not found — please install it first")
            sys.exit(1)
        else:
            print(f"  ✅ {tool} found")

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
        run("python ml/rag/financial_rag.py", cwd=".")
        print("  ✅ Knowledge base initialized")
    except Exception:
        print("  ⚠️ RAG setup skipped (Python ML deps not installed)")

    # Start Docker services
    print("\n🐳 Starting Docker services...")
    print("  This may take a few minutes on first run (pulling images)...")
    run("docker-compose up -d postgres redis")
    print("  ✅ Databases started")

    # Wait for DB
    import time
    print("  ⏳ Waiting for PostgreSQL to be ready...")
    time.sleep(10)

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("  1. Update .env with your API keys (OpenAI, Pinecone, etc.)")
    print("  2. Start all services: docker-compose up")
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
