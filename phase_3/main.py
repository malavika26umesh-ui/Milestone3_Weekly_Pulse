import time
from .database import StateManager
from datetime import datetime

def run_pulse_with_idempotency(product_id: str, iso_week: str):
    db = StateManager()
    
    print(f"--- Starting Pulse Run for {product_id} (Week {iso_week}) ---")
    
    # 1. Idempotency Check
    status = db.check_idempotency(product_id, iso_week)
    
    if status == 'SUCCESS':
        print(f"SKIP: A successful run for {product_id} in {iso_week} already exists in the database.")
        return
    elif status == 'STARTED':
        print(f"WARNING: A run for {product_id} in {iso_week} is already marked as 'STARTED'.")
        # In a real system, you might check if the timestamp is old and allow a retry
        print("Re-trying run...")
    
    # 2. Start Run
    try:
        db.start_run(product_id, iso_week)
        print("Run status: STARTED")
        
        # Simulate processing (Ingestion, ML, MCP)
        print("Processing...")
        time.sleep(2) 
        
        # 3. Complete Run
        doc_id = f"heading_id_{int(time.time())}"
        gmail_id = f"msg_id_{int(time.time())}"
        
        db.complete_run(product_id, iso_week, doc_id, gmail_id)
        print(f"Run status: SUCCESS (Doc: {doc_id}, Email: {gmail_id})")
        
    except Exception as e:
        print(f"Run status: FAILED ({e})")
        db.fail_run(product_id, iso_week)

if __name__ == "__main__":
    import sys
    product = sys.argv[1] if len(sys.argv) > 1 else "groww"
    # Get current week string e.g. "2026-W19"
    week = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y-W%V")
    
    run_pulse_with_idempotency(product, week)
