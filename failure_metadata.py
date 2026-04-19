# failure_metadata.py
FAILURE_METADATA = {
    "MISSING_RELATION": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
    },
    "WRAPPER_MISSING_PLAYER": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
    },
    "WRAPPER_MISSING_JS": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
    },
    "WRAPPER_MISSING_CSS": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
    },
    "WRAPPER_MISSING_CAST_REF": {
        "classification": "known_deterministic",
        "action": "regenerate_wrappers",
        "known": True,
    },
    "NO_CAST_FILES_FOUND": {
        "classification": "known_blocking",
        "action": "halt_missing_inputs",
        "known": True,
    },
    "CAST_MISSING_WRAPPER": {
        "classification": "known_blocking",
        "action": "halt_missing_wrapper",
        "known": True,
    },
    "WRAPPER_UNREADABLE": {
        "classification": "known_blocking",
        "action": "halt_unreadable_wrapper",
        "known": True,
    },
    "WRAPPER_DUPLICATE_PLAYER_BLOCK": {
        "classification": "known_blocking",
        "action": "manual_review",
        "known": True,
    },
}
