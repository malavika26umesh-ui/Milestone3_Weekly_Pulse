import os
import json
import time
from typing import List, Optional
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Theme(BaseModel):
    theme_name: str
    severity: str # low, medium, high
    summary: str
    representative_quotes: List[str]
    action_items: List[str]

class PulseReport(BaseModel):
    product_name: str
    iso_week: str
    themes: List[Theme]

class QuoteValidator:
    @staticmethod
    def validate(quote: str, original_reviews: List[str]) -> bool:
        """
        Validates that a quote exists verbatim in at least one original review.
        """
        quote_clean = quote.strip().lower()
        for review in original_reviews:
            if quote_clean in review.lower():
                return True
        return False

class Synthesizer:
    def __init__(self, model_name: Optional[str] = None):
        # 1. Priority: Explicitly passed model_name
        # 2. Secondary: Environment variable GEMINI_MODEL_NAME
        # 3. Default: gemini-1.5-flash
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found. Synthesizer will run in MOCK mode.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
        
    def synthesize_theme(self, cluster_reviews: List[str]) -> Optional[Theme]:
        """
        Uses Gemini to synthesize a theme from a cluster of reviews.
        Includes a delay to respect free-tier rate limits.
        """
        if not self.model:
            return self._mock_synthesis(cluster_reviews)

        # Rate limit protection: Sleep for a few seconds before each call
        # This is especially important for the free tier
        print(f"Synthesizing theme... (waiting 15s for rate limits)")
        time.sleep(15)

        prompt = f"""
        You are a Product Analyst. Analyze the following customer reviews for an app and synthesize a single cohesive theme.
        
        Reviews:
        {chr(10).join([f"- {r}" for r in cluster_reviews[:50]])}
        
        Output a JSON object with the following fields:
        - theme_name: A short, descriptive name (e.g., 'Login Latency')
        - severity: 'low', 'medium', or 'high'
        - summary: A 1-2 sentence summary of the core issue or praise.
        - representative_quotes: 2-3 verbatim quotes from the reviews that support this theme. These MUST be exact substrings from the provided reviews.
        - action_items: 2-3 specific suggestions for the product/eng team.

        Important: Output ONLY the raw JSON object. No markdown formatting, no preamble.
        """
        
        # Retry logic
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                content = response.text.strip()
                
                # Strip markdown blocks
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                theme_data = json.loads(content)
                
                # Validate quotes
                valid_quotes = [q for q in theme_data.get("representative_quotes", []) 
                               if QuoteValidator.validate(q, cluster_reviews)]
                
                if not valid_quotes and cluster_reviews:
                    valid_quotes = [cluster_reviews[0][:150]]
                    
                theme_data["representative_quotes"] = valid_quotes
                return Theme(**theme_data)
                
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait_time = (attempt + 1) * 10
                    print(f"Rate limit hit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                print(f"Error synthesizing theme: {e}")
                break
                
        return self._mock_synthesis(cluster_reviews)

    def batch_synthesize(self, cluster_groups: Dict[int, List[str]], product_name: str) -> List[Theme]:
        """
        Synthesizes all themes in a single batch API call to avoid rate limits.
        """
        if not self.model:
            return [self._mock_synthesis(texts) for texts in list(cluster_groups.values())[:3]]

        # Prepare a single massive prompt with all clusters
        clusters_text = ""
        for i, (label, texts) in enumerate(cluster_groups.items()):
            sample = "\n".join([f"- {t}" for t in texts[:20]]) # Take top 20 from each cluster
            clusters_text += f"\n### CLUSTER {i} ({len(texts)} reviews):\n{sample}\n"

        prompt = f"""
        You are a Senior Product Analyst at {product_name}. 
        I have clustered {sum(len(v) for v in cluster_groups.values())} customer reviews into semantic groups.
        
        Analyze these clusters and synthesize the top 5-7 most important themes.
        For each theme, provide:
        1. theme_name: Descriptive name.
        2. severity: 'low', 'medium', or 'high'.
        3. summary: 1-2 sentence explanation.
        4. representative_quotes: 2 verbatim quotes from the reviews.
        5. action_items: 2 suggestions for the team.

        Output ONLY a JSON list of objects matching this structure. 
        Example: [{{ "theme_name": "...", "severity": "...", ... }}]
        
        DATA:
        {clusters_text}
        """

        try:
            print(f"Performing Batch Synthesis for {product_name}... (One large API call)")
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            themes_data = json.loads(content)
            themes = []
            
            # Re-flatten all reviews for quote validation
            all_original_reviews = [r for cluster in cluster_groups.values() for r in cluster]
            
            for td in themes_data:
                # Validate quotes
                valid_quotes = [q for q in td.get("representative_quotes", []) 
                               if QuoteValidator.validate(q, all_original_reviews)]
                td["representative_quotes"] = valid_quotes or ["Quote validation failed"]
                themes.append(Theme(**td))
                
            return themes
            
        except Exception as e:
            print(f"Error in Batch Synthesis: {e}")
            return []

    def _mock_synthesis(self, cluster_reviews: List[str]) -> Theme:
        """Fallback mock response for testing without API keys."""
        return Theme(
            theme_name="Theme (Mock)",
            severity="low",
            summary=f"Synthesized from {len(cluster_reviews)} reviews.",
            representative_quotes=[cluster_reviews[0][:100]] if cluster_reviews else ["N/A"],
            action_items=["Analyze these reviews further", "Monitor for patterns"]
        )
