import sys
import os
import webbrowser
import time
import threading
import uvicorn

def open_browser():
    time.sleep(1.5)
    print("\n[*] Opening MMTPL Store ERP Portal in your default web browser...")
    webbrowser.open("http://127.0.0.1:8000")

def main():
    # Add backend directory to sys.path
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("=" * 70)
    print("  MMTPL – Store & Inventory Management ERP Portal")
    print("  Centralized Store Operations & Exact Excel Parity Engine")
    print("=" * 70)
    print("[*] Local Server: http://127.0.0.1:8000")
    print("[*] API Docs:     http://127.0.0.1:8000/docs")
    print("[*] Database:     mmtpl_store.db (SQLite with PostgreSQL compatibility)")
    print("[*] Dataset:      849 materials, 19 contractors, 1,545 inwards, 6,103 txs")
    print("[*] Calculation:  Book Balance = Booked Inward − Posted Issues + Posted Returns")
    print("=" * 70)

    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Uvicorn ASGI server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
