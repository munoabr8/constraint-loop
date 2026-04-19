
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

test:
	$(MAKE) test-smoke
	$(MAKE) test-contracts
	$(MAKE) test-taxonomy
	$(MAKE) test-orchestrator
	$(MAKE) test-orchestrator-blocking
