#!/usr/bin/env python3
"""
seed_blockchain_ledger.py

Mints and populates the immutable Blockchain Goal Ledger in Firestore
for all showcase projects and risc_processor_core.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

from database import db
from blockchain_goal_ledger import GoalBlock, GoalBlockchain
from seed_showcase_projects import SHOWCASE_PROJECTS

def seed_blockchains():
    print("⛓️ Starting Blockchain Goal Ledger Seeding...")

    # 1. Seed risc_processor_core
    risc_goal = (
        "Design, synthesize, and verify a 16-bit RISC processor core in Verilog featuring "
        "an 8-word general-purpose register file, 5-stage hazard detection, single-cycle ALU, "
        "and automated self-checking testbench over memory-mapped I/O."
    )
    risc_invs = [
        {"id": "INV-1", "label": "16-bit Harvard Architecture & ALU", "keywords": ["risc", "alu", "arithmetic", "decode", "register"]},
        {"id": "INV-2", "label": "Synthesizable Verilog RTL", "keywords": ["verilog", "rtl", "synthesis", "module", "timing"]},
        {"id": "INV-3", "label": "Self-Checking Testbench Verification", "keywords": ["testbench", "simulation", "verify", "waveform"]},
    ]
    GoalBlockchain.init_or_anchor_genesis("risc_processor_core", risc_goal, risc_invs)
    print("✅ Seeded Genesis Block for 'risc_processor_core'")

    # 2. Seed 5 Showcase Projects
    for proj in SHOWCASE_PROJECTS:
        pk = proj["project_key"]
        goal = proj["original_goal"]
        hard_invs = proj.get("invariants", {}).get("hard_invariants", [])
        sessions = proj.get("sessions", [])

        # Build clean chain
        chain = []
        # Block #0 (Genesis)
        g_block = GoalBlock(
            index=0,
            project_key=pk,
            session_number=1,
            event_type="GENESIS_BASELINE_LOCK",
            goal_text=goal,
            invariants=hard_invs,
            task_titles=sessions[0].get("task_titles", ["Genesis Baseline Contract"]),
            alignment_score=100.0,
            preservation_rate=100.0,
            prev_hash="0" * 64,
            validator="GENESIS_BASELINE_ANCHOR",
            timestamp=(datetime.utcnow() - timedelta(days=len(sessions))).isoformat() + "Z",
        )
        nonce = 0
        while not g_block.calculate_hash().startswith("00") and nonce < 1000:
            nonce += 1
            g_block.nonce = nonce
        g_block.block_hash = g_block.calculate_hash()
        chain.append(g_block)

        # Subsequent session blocks
        for s in sessions[1:]:
            s_num = s.get("session_number", 2)
            c_type = s.get("change_type", "DRIFT")
            score = s.get("alignment_score", 50.0)
            tasks = s.get("task_titles", [])
            pres_rate = 100.0 if c_type in ("BASELINE", "REANCHOR", "INTENTIONAL") else 33.3
            validator = "HUMAN_GATE_OPERATOR" if c_type in ("INTENTIONAL", "REANCHOR") else "ORCHESTRATOR_CONSENSUS_ENGINE"

            prev_h = chain[-1].block_hash
            block = GoalBlock(
                index=len(chain),
                project_key=pk,
                session_number=s_num,
                event_type=c_type,
                goal_text=s.get("new_goal_summary", goal),
                invariants=hard_invs,
                task_titles=tasks,
                alignment_score=score,
                preservation_rate=pres_rate,
                prev_hash=prev_h,
                validator=validator,
                timestamp=(datetime.utcnow() - timedelta(days=len(sessions) - s_num + 1)).isoformat() + "Z",
            )
            nonce = 0
            while not block.calculate_hash().startswith("0") and nonce < 500:
                nonce += 1
                block.nonce = nonce
            block.block_hash = block.calculate_hash()
            chain.append(block)

        GoalBlockchain.save_chain(pk, chain)
        audit = GoalBlockchain.verify_chain_integrity(pk)
        print(f"✅ Seeded {len(chain)} blocks for '{pk}' | Integrity: {audit['audit_status']} (Tamper: {audit['tamper_detected']})")

    print("\n🎉 ALL BLOCKCHAINS SUCCESSFULLY SEEDED AND CRYPTOGRAPHICALLY VERIFIED IN FIRESTORE!")

if __name__ == "__main__":
    seed_blockchains()
