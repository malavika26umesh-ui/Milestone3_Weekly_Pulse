from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np
from typing import List, Tuple, Dict
from .pii_scrubber import scrub_pii

class ClusteringEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # This will use the already installed sentence-transformers
        self.model = SentenceTransformer(model_name)
        
    def process_reviews(self, review_texts: List[str], n_clusters: int = 10) -> Tuple[np.ndarray, List[int]]:
        """
        Processes reviews and returns embeddings and K-Means cluster labels.
        """
        # 1. Scrub PII
        scrubbed_texts = [scrub_pii(t) for t in review_texts]
        
        # 2. Generate Embeddings
        print(f"Generating embeddings for {len(scrubbed_texts)} reviews...")
        embeddings = self.model.encode(scrubbed_texts, show_progress_bar=True)
        
        # 3. K-Means Clustering
        # We use a fixed or dynamic number of clusters
        # For ~1000 reviews, 10-15 clusters is usually ideal
        actual_n_clusters = min(n_clusters, len(review_texts))
        print(f"Clustering into {actual_n_clusters} themes using K-Means...")
        
        kmeans = KMeans(n_clusters=actual_n_clusters, random_state=42, n_init='auto')
        labels = kmeans.fit_predict(embeddings)
        
        return embeddings, labels.tolist()

    def get_cluster_groups(self, review_texts: List[str], labels: List[int]) -> Dict[int, List[str]]:
        """
        Groups reviews by their cluster labels.
        """
        clusters = {}
        for text, label in zip(review_texts, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(text)
        return clusters
