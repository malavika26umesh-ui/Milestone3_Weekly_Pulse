# Weekly Product Review Pulse — Phase-wise Edge Cases

This document identifies potential edge cases for each phase and outlines the mitigation or handling strategy.

---

## Phase 1: Foundation & Data Ingestion
*   **Edge Case: Zero Reviews in Week**: If a product has no reviews in the window, the system should log a "No Data" status and skip delivery, rather than failing or sending an empty report.
*   **Edge Case: Bot/Spam Flooding**: A sudden spike of 1,000+ identical reviews.
    *   *Handling*: Implement basic deduplication during ingestion.
*   **Edge Case: App Store RSS Change**: The RSS feed structure changes or becomes unavailable.
    *   *Handling*: Robust error handling and alerting for ingestion failures.

## Phase 2: ML & AI Processing Pipeline
*   **Edge Case: Tiny Cluster Size**: A cluster with only 1-2 reviews.
    *   *Handling*: Filter out clusters below a minimum density threshold (e.g., < 3 reviews) as "insignificant feedback".
*   **Edge Case: LLM Quote Hallucination**: The LLM creates a "perfect" quote that doesn't exist.
    *   *Handling*: The Quote Validator must discard the quote and request a retry or fallback to the most representative review.
*   **Edge Case: Multi-Language Reviews**: Reviews in languages other than English.
    *   *Handling*: Initial scope is English-only. Non-English reviews should be filtered or flagged.

## Phase 3: State Management & Idempotency
*   **Edge Case: Interrupted Run**: System crashes halfway through a Docs append but before the DB is updated.
    *   *Handling*: Use "STARTED" status with a timeout. If a run stays "STARTED" for > 30 mins, it is eligible for retry.
*   **Edge Case: Database Lock**: Multiple instances of the CLI trying to write to the same SQLite file.
    *   *Handling*: Implement file-based locking or rely on SQLite's internal locking with a wait timeout.

## Phase 4: MCP Integration (Google Docs)
*   **Edge Case: Document Deleted**: The "System of Record" Doc is deleted or moved.
    *   *Handling*: Check document existence before append. If missing, create a new one and update the configuration.
*   **Edge Case: Quota Limits**: Exceeding Google Docs API rate limits during a bulk backfill.
    *   *Handling*: Implement exponential backoff in the MCP server or the client.

## Phase 5: MCP Integration (Gmail)
*   **Edge Case: Invalid Recipient List**: Stakeholder email list is empty or contains malformed addresses.
    *   *Handling*: Validate email addresses before calling the MCP tool.
*   **Edge Case: Threading Collision**: Sending a new email that mistakenly threads into an unrelated conversation.
    *   *Handling*: Ensure each pulse email has a unique, week-specific subject line.

## Phase 6: Orchestration & CLI
*   **Edge Case: Conflicting Date Windows**: Running a backfill that overlaps with an already-completed week.
    *   *Handling*: The Idempotency logic must be week-aware, not just run-aware.
*   **Edge Case: Network Timeout during MCP Call**:
    *   *Handling*: Implement a robust retry mechanism (Max 3 retries) with a clear error log for manual intervention.
