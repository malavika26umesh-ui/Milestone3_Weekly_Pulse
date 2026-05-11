import json
import os
from dotenv import load_dotenv
from .clustering_engine import ClusteringEngine
from .synthesizer import Synthesizer, PulseReport
from datetime import datetime

load_dotenv()

def run_processing(data_file: str, product_name: str):
    if not os.path.exists(data_file):
        print(f"File {data_file} not found.")
        return

    # 1. Load Data
    with open(data_file, "r", encoding="utf-8") as f:
        reviews_data = json.load(f)
    
    review_texts = [r['content'] for r in reviews_data]
    print(f"Loaded {len(review_texts)} reviews for processing.")

    # 2. Cluster
    engine = ClusteringEngine()
    embeddings, labels = engine.process_reviews(review_texts)
    cluster_groups = engine.get_cluster_groups(review_texts, labels)
    
    print(f"Found {len(cluster_groups)} clusters (excluding noise).")

    # 3. Synthesize Themes (Batch Mode)
    synthesizer = Synthesizer()
    print("Synthesizing themes using Batch Mode (Single API Call)...")
    themes = synthesizer.batch_synthesize(cluster_groups, product_name)
    
    print(f"Successfully synthesized {len(themes)} themes.")

    # 4. Generate Final Report
    report = PulseReport(
        product_name=product_name,
        iso_week=datetime.now().strftime("%Y-W%V"),
        themes=themes
    )

    # 5. Save Report
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/{product_name.lower()}_pulse_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode='json'), f, indent=4)
    
    print(f"Successfully generated pulse report: {report_file}")
    return report_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m phase_2.main <data_file> <product_name>")
    else:
        run_processing(sys.argv[1], sys.argv[2])
