# Weekly Product Review Pulse — Phase-wise Evaluations

This document defines the metrics and validation criteria for each phase of the project to ensure the system meets high quality and performance standards.

---

## Phase 1: Foundation & Data Ingestion
*   **Metric: Ingestion Completeness**: Compare fetched review counts against manual checks on App Store/Play Store web versions.
*   **Metric: Schema Accuracy**: 100% of fetched reviews must pass `Pydantic` validation without errors.
*   **Validation**: Verify that the time windowing logic correctly filters reviews exactly within the specified 8-12 week range.

## Phase 2: ML & AI Processing Pipeline
*   **Metric: PII Scrubbing Recall**: Manually check a sample of 100 reviews; no phone numbers or email addresses should remain.
*   **Metric: Cluster Cohesion**: Evaluate the "Silhouette Score" or manual relevance of reviews within a cluster (do they all talk about the same thing?).
*   **Metric: Quote Integrity**: 100% pass rate for the Quote Validator (LLM quotes must exist in source text).
*   **Metric: Actionability**: Stakeholder review of "Action Ideas" to ensure they are practical and non-generic.

## Phase 3: State Management & Idempotency
*   **Metric: Run Consistency**: Re-running a completed week must result in zero external tool calls (Docs/Gmail).
*   **Validation**: Corrupt a run in the DB to "FAILED" and verify that the orchestrator correctly picks it up for a retry.

## Phase 4: MCP Integration (Google Docs)
*   **Metric: Formatting Fidelity**: Visual check of the Google Doc to ensure headings are properly nested and bullet points are correctly rendered.
*   **Metric: Append Latency**: Time taken for the MCP call to complete (target < 5 seconds per append).
*   **Validation**: Verify that appending to a very large document does not cause timeouts or styling issues.

## Phase 5: MCP Integration (Gmail)
*   **Metric: Link Validity**: Verify the "Read Full Report" link points exactly to the correct heading/anchor in the Google Doc.
*   **Metric: Template Rendering**: Check email rendering across different clients (Gmail Web, Mobile, Desktop).

## Phase 6: Orchestration & CLI
*   **Metric: E2E Reliability**: Success rate of 10 consecutive full runs across different products.
*   **Metric: Resource Usage**: Monitor token usage per run to ensure it stays within budget limits.
*   **Validation**: Test the `backfill` command for a 4-week range to ensure state is correctly tracked for each individual week.

## Phase 7: Testing & Refinement
*   **Metric: Ground Truth Comparison**: Compare LLM-generated themes against a manually categorized set of reviews.
*   **Metric: User Acceptance**: Product/Support teams confirm the "Weekly Pulse" provides value they couldn't get from raw data.
