#!/usr/bin/env python3

FAILURE_METADATA = {
    "MISSING_RELATION": {
        "classification": "known_deterministic",
        "action": "repair_wrapper",
        "known": True,
        "executor": "repairer",
    },
    "WRAPPER_MISSING_PLAYER": {
        "classification": "known_deterministic",
        "action": "repair_wrapper",
        "known": True,
        "executor": "repairer",
    },
    "WRAPPER_MISSING_JS": {
        "classification": "known_deterministic",
        "action": "repair_wrapper",
        "known": True,
        "executor": "repairer",
    },
    "WRAPPER_MISSING_CSS": {
        "classification": "known_deterministic",
        "action": "repair_wrapper",
        "known": True,
        "executor": "repairer",
    },
    "WRAPPER_MISSING_CAST_REF": {
        "classification": "known_deterministic",
        "action": "repair_wrapper",
        "known": True,
        "executor": "repairer",
    },
    "NO_CAST_FILES_FOUND": {
        "classification": "known_blocking",
        "action": "halt_missing_inputs",
        "known": True,
        "executor": "none",
    },
    "CAST_MISSING_WRAPPER": {
        "classification": "known_blocking",
        "action": "halt_missing_wrapper",
        "known": True,
        "executor": "none",
    },
    "WRAPPER_UNREADABLE": {
        "classification": "known_blocking",
        "action": "halt_unreadable_wrapper",
        "known": True,
        "executor": "none",
    },
    "WRAPPER_DUPLICATE_PLAYER_BLOCK": {
        "classification": "known_blocking",
        "action": "manual_review",
        "known": True,
        "executor": "none",
    },
}