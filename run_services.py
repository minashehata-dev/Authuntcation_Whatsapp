import subprocess
import sys
import os
import signal
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PYTHON_EXE = sys.executable

def main():
    print("=" * 65)
    print("🚀 Starting WhatsApp OTP Verification System")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    gateway_dir = os.path.join(base_dir, "whatsapp_gateway")
    app_dir = os.path.join(backend_dir, "app")

    # Set up Python environment variables
    env = os.environ.copy()
    python_paths = [backend_dir, app_dir]
    if "PYTHONPATH" in env:
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    # 1. Start Node.js Baileys Gateway
    print("\n[1/2] 🟢 Starting Baileys WhatsApp Gateway (Node.js)...")
    node_cmd = ["node", "src/index.js"]
    gateway_proc = subprocess.Popen(
        node_cmd,
        cwd=gateway_dir
    )

    time.sleep(2)

    # 2. Start Python FastAPI Backend
    print("\n[2/2] 🟢 Starting Python FastAPI Backend Server...")
    python_cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
    ]
    backend_proc = subprocess.Popen(
        python_cmd,
        cwd=backend_dir,
        env=env
    )

    print("\n" + "=" * 65)
    print("✅ All services are starting up!")
    print("📱 Baileys Gateway: http://localhost:3001 (QR code at /api/qr)")
    print("⚡ Python Backend:  http://localhost:8000")
    print("📖 Swagger Docs:    http://localhost:8000/docs")
    print("=" * 65)
    print("Press Ctrl+C to terminate both services.\n")

    try:
        while True:
            time.sleep(1)
            if gateway_proc.poll() is not None:
                print("❌ Gateway process terminated.")
                break
            if backend_proc.poll() is not None:
                print("❌ Backend process terminated.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
    finally:
        gateway_proc.terminate()
        backend_proc.terminate()
        try:
            gateway_proc.wait(timeout=3)
            backend_proc.wait(timeout=3)
        except Exception:
            gateway_proc.kill()
            backend_proc.kill()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
