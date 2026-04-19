test-smoke:
	./tests/smoke_taxonomy.sh

test-contracts:
	./tests/test_constraint_loop_contracts.sh

test-taxonomy:
	./tests/test_failure_metadata_consistency.sh

test:
	$(MAKE) test-smoke
	$(MAKE) test-contracts
	$(MAKE) test-taxonomy
