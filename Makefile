
.PHONY: test test-smoke test-contracts test-taxonomy test-orchestrator

test-smoke:
	./tests/smoke_taxonomy.sh

test-contracts:
	./tests/test_constraint_loop_contracts.sh

test-taxonomy:
	./tests/test_failure_metadata_consistency.sh

test-orchestrator:
	./tests/test_run_constraint_loop.sh

test-orchestrator-blocking:
	./tests/test_run_constraint_loop_blocking.sh

test-orchestrator-unknown:
	./tests/test_run_constraint_loop_unknown.sh

test-orchestrator-nonblocking:
	./tests/test_run_constraint_loop_nonblocking.sh

test-orchestrator-recovered:
	./tests/test_run_constraint_loop_recovered.sh

test-artifact-schema:
	./tests/test_run_artifact_schema.sh

test-orchestrator-unknown2:
	./tests/test_run_constraint_loop_unknown2.sh

test:
	$(MAKE) test-smoke
	$(MAKE) test-contracts
	$(MAKE) test-taxonomy
	$(MAKE) test-orchestrator
	$(MAKE) test-orchestrator-nonblocking
	$(MAKE) test-orchestrator-recovered
	$(MAKE) test-orchestrator-blocking
	$(MAKE) test-artifact-schema
	#$(MAKE) test-orchestrator-unknown2
	#$(MAKE) test-artifact-schema-blocking
	#$(MAKE) test-checker-head
