import asyncio
import sys
import os
import argparse
from datetime import datetime
from phase_1.main import run_ingestion
from phase_2.main import run_processing
from phase_3.database import StateManager
from phase_4.client import DocsMCPClient
from phase_5.client import GmailMCPClient

# Replace this with your actual Google Doc ID to collect all pulses in one place
MASTER_DOC_ID = "15ZLTkFdJw3RlpC8F5ATbNRm7v9zI2J9LVerR4d-wm2k"
print("[DEBUG] Running Pulse Orchestrator v2.0 (Lowercase Fix Applied)")

class PulseOrchestrator:
    def __init__(self):
        self.db = StateManager()
        self.docs_client = DocsMCPClient("phase_4/server.py")
        self.gmail_client = GmailMCPClient("phase_5/server.py")

    def get_current_week(self):
        return datetime.now().strftime("%Y-W%W")

    async def run(self, product_name: str, force: bool = False):
        iso_week = self.get_current_week()
        print(f"\n[START] Starting Weekly Pulse for {product_name} ({iso_week})")

        # 1. Idempotency Check
        state = self.db.check_idempotency(product_name, iso_week)
        if state == "SUCCESS" and not force:
            print(f"[SKIP] Pulse already completed for {product_name} in {iso_week}.")
            return

        self.db.start_run(product_name, iso_week)

        try:
            # 2. Phase 1: Ingestion
            print("\n--- Phase 1: Ingestion & Filtering ---")
            raw_data_path = run_ingestion(product_name)
            if not raw_data_path or not os.path.exists(raw_data_path):
                raise Exception("Ingestion failed to produce data.")

            # 3. Phase 2: AI Processing
            print("\n--- Phase 2: AI Synthesis ---")
            report_path = run_processing(raw_data_path, product_name)
            if not report_path or not os.path.exists(report_path):
                raise Exception("AI Processing failed to produce report.")

            # 4. Delivery (Phase 4 & 5 via MCP)
            print("\n--- Phase 4/5: MCP Delivery ---")
            import json
            with open(report_path, 'r') as f:
                report_data = json.load(f)

            # Generate Doc Content
            doc_title = f"{product_name} Weekly Pulse - {iso_week}"
            doc_content = ""
            
            for theme in report_data.get("themes", []):
                doc_content += f"## {theme['theme_name']} ({theme['severity'].upper()})\n"
                doc_content += f"{theme['summary']}\n\n"
                doc_content += "**Representative Quotes:**\n"
                for q in theme['representative_quotes']:
                    doc_content += f"- \"{q}\"\n"
                doc_content += "\n**Action Items:**\n"
                for a in theme['action_items']:
                    doc_content += f"- {a}\n"
                doc_content += "\n---\n\n"
            

            # 4a. Google Docs
            print("Updating Google Doc...")
            doc_result_raw = await self.docs_client.append_report(MASTER_DOC_ID, doc_title, doc_content)
            print(f"Docs MCP: {doc_result_raw}")
            
            # Parse Doc Result for Deep Linking
            try:
                doc_info = json.loads(doc_result_raw)
                doc_id = doc_info.get("document_id", MASTER_DOC_ID)
                bookmark_id = doc_info.get("bookmark_id", "")
                if bookmark_id:
                    doc_link = f"https://docs.google.com/document/d/{doc_id}/edit#bookmark=id.{bookmark_id}"
                else:
                    doc_link = f"https://docs.google.com/document/d/{doc_id}/edit"
            except:
                doc_link = f"https://docs.google.com/document/d/{MASTER_DOC_ID}/edit"

            # 4b. Gmail Draft Content
            print("Preparing Delivery Content...")
            
            # Simple Markdown to HTML conversion for the email
            html_content = doc_content
            import re
            
            # Convert headings
            html_content = re.sub(r'^## (.*)$', r'<h2 style="color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;">\1</h2>', html_content, flags=re.MULTILINE)
            # Convert bold
            html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
            # Convert lists
            html_content = re.sub(r'^- (.*)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
            html_content = html_content.replace('<li>', '<ul style="margin-top: 0;"><li>', 1) # Start first list
            html_content = re.sub(r'</li>\n\n', r'</li></ul>\n\n', html_content) # Close lists
            
            # Final fallback for newlines
            html_content = html_content.replace('\n', '<br>')

            email_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-bottom: 1px solid #e0e0e0;">
                            <h1 style="color: #1a73e8; margin: 0; font-size: 24px;">{doc_title}</h1>
                        </div>
                        
                        <div style="padding: 20px;">
                            <p>The weekly insight report for <strong>{product_name}</strong> is now available.</p>
                            
                            <div style="margin: 25px 0; text-align: center;">
                                <a href="{doc_link}" style="background-color: #1a73e8; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 16px;">
                                    View Full Report in Google Docs
                                </a>
                            </div>

                            <div style="background: #ffffff; padding: 15px; border: 1px solid #f0f0f0; border-radius: 6px;">
                                {html_content}
                            </div>
                        </div>
                        
                        <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0;">
                            <p>This is an automated pulse generated by the Weekly Product Pulse system.</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Save Local Previews
            preview_html_path = f"reports/{product_name}_email_preview_{iso_week}.html"
            preview_md_path = f"reports/{product_name}_report_preview_{iso_week}.md"
            
            with open(preview_html_path, 'w', encoding='utf-8') as f:
                f.write(email_body)
            with open(preview_md_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
                
            print(f"[SAVE] Local previews saved to {preview_html_path} and {preview_md_path}")

            # 4c. Gmail Draft
            print("Creating Gmail Draft...")
            gmail_result = await self.gmail_client.create_draft(
                "stakeholders@example.com", 
                f"Pulse Report: {product_name} ({iso_week})", 
                email_body
            )
            print(f"Gmail MCP: {gmail_result}")

            # 5. Finalize State
            self.db.complete_run(product_name, iso_week, str(doc_result_raw), str(gmail_result))
            print(f"\n[FINISH] Weekly Pulse for {product_name} completed successfully!")

        except Exception as e:
            print(f"\n[ERROR] Error during Pulse execution: {e}")
            self.db.fail_run(product_name, iso_week)
            raise

async def main():
    parser = argparse.ArgumentParser(description="Weekly Product Review Pulse Orchestrator")
    parser.add_argument("--product", required=True, help="Name of the product (e.g., Groww)")
    parser.add_argument("--force", action="store_true", help="Force run even if already successful for this week")
    
    args = parser.parse_args()
    
    # Import PRODUCTS from phase_1 to check valid options
    from phase_1.main import PRODUCTS
    
    product_key = args.product.lower()
    if product_key not in PRODUCTS:
        print(f"\n[ERROR] Product '{args.product}' not found in products_config.json")
        print(f"Available options: {', '.join(PRODUCTS.keys())}")
        sys.exit(1)

    orchestrator = PulseOrchestrator()
    await orchestrator.run(args.product, args.force)

if __name__ == "__main__":
    asyncio.run(main())
