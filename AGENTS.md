# Tradeverse Agent Rules & Continuous Knowledge Ingestion

## MANDATORY PROTOCOL: Continuous Lessons Learned Recording

Whenever any trading rule, risk safeguard, post-mortem finding, or algorithmic execution logic is modified, optimized, or created in Tradeverse:

1. **Update Vector Memory (RAG Engine):**
   - Append the rule/lesson into `backend/rag_engine.py` in the `SEED_JOURNAL` list under the `trader_journal` collection.
   - Tag with relevant metadata (`author: "post_mortem"`, `priority: "critical"`, `date: "YYYY-MM-DD"`).

2. **Update Lessons Learned UI:**
   - Add the new post-mortem / optimization category into `frontend/src/components/LessonsLearned.jsx`.
   - Re-run `npm run build` in `frontend/` to keep production distribution assets up to date.

3. **Deploy to Production Cloud Engine:**
   - When core execution files (such as `main.py`, `rag_engine.py`, `angel_client.py`, `risk_engine.py`) are modified, deploy the file to the Oracle Cloud 24/7 VM (`129.225.125.13`) via `scp` and verify engine pulse via `/api/cloud/pulse`.

4. **Version Control Audit Trail:**
   - Commit all changes to Git with structured commit messages documenting the rationale and date.
