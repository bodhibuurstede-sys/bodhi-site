#!/usr/bin/env python3
"""Small reproducible demo for RustChain's public PoA hardware validator.

Run from the root of a clone of https://github.com/Scottcjn/Rustchain:

    python path/to/rustchain-hardware-proof-demo.py

The script imports the repository's current validator and exercises one
classic-like and one modern-like synthetic signal bundle. It does not mine,
submit an attestation, or contact a network.
"""

from node.rip_proof_of_antiquity_hardware import server_side_validation


def entropy_hex() -> str:
    # All 256 byte values once -> 8 bits/byte Shannon entropy.
    return bytes(range(256)).hex()


classic_payload = {
    "device": {"arch": "ppc", "family": "demo"},
    "signals": {
        "entropy_samples": entropy_hex(),
        "cpu_timing": {
            "samples": [8470, 8480, 8490, 8500, 8510, 8520, 8530, 8500, 8500, 8500]
        },
        "ram_timing": {
            "sequential_ns": 350,
            "random_ns": 1400,
            "cache_hit_rate": 0.50,
        },
        "macs": ["02:00:00:00:00:01"],
    },
}

modern_payload = {
    "device": {"arch": "x86_64", "family": "demo"},
    "signals": {
        "entropy_samples": entropy_hex(),
        "cpu_timing": {
            "samples": [492, 496, 498, 500, 502, 504, 508, 500, 500, 500]
        },
        "ram_timing": {
            "sequential_ns": 80,
            "random_ns": 150,
            "cache_hit_rate": 0.95,
        },
        "macs": ["02:00:00:00:00:02"],
    },
}


for label, payload in (("classic-like", classic_payload), ("modern-like", modern_payload)):
    accepted, result = server_side_validation(payload)
    print(f"{label}: accepted={accepted}")
    print(f"  tier={result['antiquity_tier']}")
    print(f"  multiplier={result['reward_multiplier']}")
    print(f"  entropy_score={result['entropy_score']:.3f}")
    print(f"  confidence={result['confidence']:.3f}")
    print(f"  warnings={result['warnings']}")

assert server_side_validation(classic_payload)[0] is True
assert server_side_validation(classic_payload)[1]["antiquity_tier"] == "classic"
assert server_side_validation(modern_payload)[0] is True
assert server_side_validation(modern_payload)[1]["antiquity_tier"] == "modern"

print("demo assertions passed")
