Required top-level keys:
- started_at
- artifacts_dir
- check_output
- classification_output
- handler_output
- final_status
- final_decision
- repaired_any

Conditional keys:
- repair_output: present for repair-attempted paths
- recheck_output: present after repair attempts

Known final_decision values:
- already_valid
- recovered
- repair_failed
- halt
- escalate
- no_repair_path