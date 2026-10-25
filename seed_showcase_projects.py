#!/usr/bin/env python3
"""
seed_showcase_projects.py

Populates live Google Cloud Firestore with 5 distinct deep-tech R&D showcase projects.
Each project includes:
- Authentic goal_state with hard invariants (INV-1..3) & soft scope (SCOPE-1..2)
- Multi-session lineage (Session 1: BASELINE -> Session 2: DRIFT -> Session 3: REANCHOR -> Session 4: INTENTIONAL)
- Real time-machine rollback capabilities (⏪ Rollback to S1/S2/S3)
- Rich run_history entries for the sidebar Past Runs panel

Leaves 'risc_processor_core' clean at Session 1 (BASELINE 100%) for live demo execution.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure environment is loaded from the script directory
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from database import db, log_run_history
from goal_tracking import _get_embedding, _goal_version_hash
from google.cloud.firestore_v1.base_query import FieldFilter


SHOWCASE_PROJECTS = [
    {
        "project_key": "quantum_qubit_cryo_ctrl",
        "title": "Cryogenic Transmon Qubit Pulse Controller",
        "original_goal": "Design a cryogenic pulse controller for superconducting transmon qubits operating below 20mK with sub-10ns pulse fidelity and <0.1% gate error.",
        "invariants": {
            "hard_invariants": [
                {
                    "id": "INV-1",
                    "label": "Cryostat Thermal Dissipation Limit (<1 uW per control line at 20 mK)",
                    "description": "Total parasitic dissipation on dilution refrigerator mixing chamber must not exceed 1 uW per coaxial line to preserve 15 mK base temperature.",
                    "keywords": ["cryostat", "thermal budget", "20mk", "cryogenic", "dissipation", "thermal parasitic", "1 uW"],
                },
                {
                    "id": "INV-2",
                    "label": "Sub-10ns Microwave Pulse Fidelity (>= 99.9% single-qubit fidelity)",
                    "description": "DRAG-corrected microwave drive envelope must maintain >= 99.9% randomized benchmarking gate fidelity under 10 ns duration.",
                    "keywords": ["sub-10ns", "fidelity", "microwave", "pulse shape", "transmon", "gate error", "pulse modulator"],
                },
                {
                    "id": "INV-3",
                    "label": "Superconducting Interconnect Routing (<0.5 dB insertion loss)",
                    "description": "Superconducting NbTi coaxial microwave lines between 4K stage and mixing chamber must exhibit insertion loss below 0.5 dB.",
                    "keywords": ["superconducting", "interconnect", "insertion loss", "rf line", "cryo-lna", "nbti"],
                },
            ],
            "soft_scope": [
                {
                    "id": "SCOPE-1",
                    "label": "Real-time Qubit Flux Bias Tuning",
                    "description": "Fast flux bias DAC channel for dynamical two-qubit CZ gate tuning and frequency parking.",
                    "keywords": ["flux bias", "z-pulse", "flux-tunable", "qubit coupler", "cz gate"],
                },
                {
                    "id": "SCOPE-2",
                    "label": "Automated Dispersive Readout DSP Pipeline",
                    "description": "Demodulation filter and low-latency state discriminator on room-temperature FPGA.",
                    "keywords": ["dispersive readout", "dsp filter", "readout cavity", "fpga", "state discriminator"],
                },
            ],
        },
        "sessions": [
            {
                "session_number": 1,
                "change_type": "BASELINE",
                "alignment_score": 100.0,
                "old_goal_summary": "",
                "new_goal_summary": "Anchored baseline transmon qubit cryogenic control architecture.",
                "reason": "Baseline goal and cryogenic physical invariant contracts anchored.",
                "task_titles": [
                    "Qubit Pulse Modulator Spec",
                    "Cryostat Thermal Budget Analysis (<20mK)",
                    "Sub-10ns Microwave Waveform Generator",
                    "Superconducting Interconnect Routing Plan",
                ],
                "time_offset_hours": -6,
            },
            {
                "session_number": 2,
                "change_type": "DRIFT",
                "alignment_score": 38.4,
                "old_goal_summary": "Cryogenic transmon qubit controller (<20mK)",
                "new_goal_summary": "Room-temp CMOS RF driver benchmarking and standard ambient DSP filtering.",
                "reason": "Severe Scope Drift: Focus shifted to ambient CMOS RF circuits, violating the sub-20mK cryostat thermal envelope and pulse fidelity limits.",
                "task_titles": [
                    "Room-temp CMOS Driver Benchmarking",
                    "DSP Filter Optimization for Standard Ambient",
                    "High-power RF amplifier integration",
                ],
                "time_offset_hours": -4,
            },
            {
                "session_number": 3,
                "change_type": "REANCHOR",
                "alignment_score": 88.5,
                "old_goal_summary": "Room-temp CMOS RF driver benchmarking",
                "new_goal_summary": "Re-anchored: SiGe BiCMOS Cryo-ASIC operating at 4K stage with superconducting interconnects.",
                "reason": "Contract Re-anchored: Downstream thermal budget restored via SiGe cryogenic ASIC operating at the 4K stage with superconducting interconnects.",
                "task_titles": [
                    "SiGe BiCMOS Cryo-ASIC Blueprint (<20mK cryostat thermal budget)",
                    "Low-power Cryo-LNA Integration with superconducting interconnect routing",
                    "Thermal Parasitics Modeling at 4K/20mK stages (<1 uW dissipation)",
                    "Sub-10ns microwave pulse shape fidelity optimizer",
                ],
                "time_offset_hours": -2,
            },
            {
                "session_number": 4,
                "change_type": "INTENTIONAL",
                "alignment_score": 95.2,
                "old_goal_summary": "SiGe BiCMOS Cryo-ASIC operating at 4K stage",
                "new_goal_summary": "Expanded scope to include fast flux bias tuning DAC for two-qubit CZ gates.",
                "reason": "Approved Scope Evolution: Added fast flux pulse channel compliant with sub-1uW thermal limits to enable two-qubit entangling gates.",
                "task_titles": [
                    "Flux bias z-pulse DAC implementation for two-qubit CZ gates",
                    "Sub-10ns microwave pulse fidelity transmon gate error verification",
                    "Cryostat thermal budget (<20mK) dissipation limit verification",
                    "Superconducting interconnect insertion loss analysis",
                ],
                "time_offset_hours": -0.5,
            },
        ],
        "run_history": {
            "prompt": "Design cryogenic pulse controller for superconducting transmon qubits operating below 20mK",
            "summary": "Synthesized cryogenic control architecture for multi-qubit transmon array. Operating at 15 mK dilution refrigerator mixing chamber stage with sub-10ns pulse shaping, ultra-low 0.4 uW dissipation per line, and SiGe low-noise amplification.",
            "duration_seconds": 21.8,
            "notion": {
                "hub_page_url": "https://www.notion.so/Autonomous-R-D-Runs-Hub-quantum_qubit_cryo_ctrl",
                "run_page_url": "https://www.notion.so/Run-Workspace-quantum_qubit_cryo_ctrl",
                "kanban_database_id": "9a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
            },
            "calendar_event_links": [
                {
                    "title": "Cryogenic Thermal Budget Review (<20mK)",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Tomorrow at 10:00 AM IST",
                },
                {
                    "title": "Microwave Pulse Fidelity Benchmarking",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Thursday at 2:30 PM IST",
                },
            ],
        },
    },
    {
        "project_key": "crispr_cas13_rna_sensor",
        "title": "Microfluidic Cas13a Rapid RNA Biosensor",
        "original_goal": "Develop a microfluidic Cas13a biosensor platform for rapid optical detection of airborne viral RNA with sub-femtomolar sensitivity within 15 minutes.",
        "invariants": {
            "hard_invariants": [
                {
                    "id": "INV-1",
                    "label": "Sub-femtomolar Detection Limit (<= 10 fM target RNA sensitivity)",
                    "description": "Cas13a collateral cleavage of quenched fluorescent reporters must resolve target concentration down to 10 fM.",
                    "keywords": ["femtomolar", "sensitivity", "detection limit", "cas13a", "crrna", "target rna", "fluorescent cleavage"],
                },
                {
                    "id": "INV-2",
                    "label": "Rapid Diagnostic Latency (<15 minutes time-to-result)",
                    "description": "Complete assay pipeline from sample inlet to fluorescence readout must complete within 15 minutes.",
                    "keywords": ["15 minutes", "rapid", "time-to-result", "cleavage assay", "12 minutes", "latency"],
                },
                {
                    "id": "INV-3",
                    "label": "Isothermal Enzymatic Reaction (37C operation without thermal cycling)",
                    "description": "Amplification and reporter cleavage must proceed isothermally at 37°C without peltier thermal cycling.",
                    "keywords": ["isothermal", "37c", "enzymatic", "rpa", "recombinase", "reaction chamber"],
                },
            ],
            "soft_scope": [
                {
                    "id": "SCOPE-1",
                    "label": "Smartphone Optical Fluorometer Reader Interface",
                    "description": "Clip-on 3D-printed fluorometer lens attachment with automated fluorescence image processing app.",
                    "keywords": ["smartphone", "optical reader", "fluorometer", "mobile app"],
                },
                {
                    "id": "SCOPE-2",
                    "label": "Disposable Injection-Molded PDMS Cartridge",
                    "description": "Disposable microfluidic capillary cartridge with lyophilized reagent chambers.",
                    "keywords": ["cartridge", "pdms", "microfluidic channel", "disposable", "capillary"],
                },
            ],
        },
        "sessions": [
            {
                "session_number": 1,
                "change_type": "BASELINE",
                "alignment_score": 100.0,
                "old_goal_summary": "",
                "new_goal_summary": "Anchored microfluidic Cas13a diagnostic biosensor architecture.",
                "reason": "Baseline diagnostic protocol and isothermal sensitivity invariants anchored.",
                "task_titles": [
                    "Cas13a-crRNA Complex Lyophilization Protocol",
                    "Microfluidic Capillary Channel Design",
                    "Fluorescent Cleavage Assay Model",
                    "Isothermal 37C Reaction Chamber Spec",
                ],
                "time_offset_hours": -5,
            },
            {
                "session_number": 2,
                "change_type": "DRIFT",
                "alignment_score": 35.8,
                "old_goal_summary": "Microfluidic Cas13a isothermal RNA biosensor (<15 mins)",
                "new_goal_summary": "Dual-peltier PCR thermal cycling instrumentation and gel electrophoresis.",
                "reason": "Critical Drift: Shifted to high-temperature PCR amplification, breaching isothermal requirement and 15-minute diagnostic deadline.",
                "task_titles": [
                    "Taq Polymerase Master Mix Setup",
                    "Dual-peltier PCR Thermal Cycling Unit",
                    "Gel Electrophoresis Verification",
                ],
                "time_offset_hours": -3,
            },
            {
                "session_number": 3,
                "change_type": "REANCHOR",
                "alignment_score": 92.4,
                "old_goal_summary": "Dual-peltier PCR thermal cycling instrumentation",
                "new_goal_summary": "Re-anchored: Isothermal Recombinase Polymerase Amplification (RPA) + Cas13a cleavage cascade.",
                "reason": "Contract Re-anchored: Replaced thermal cycling with recombinase polymerase amplification (RPA), achieving 5 fM sensitivity in 12 minutes.",
                "task_titles": [
                    "Cas13a-crRNA collateral cleavage assay & sub-femtomolar target RNA sensitivity",
                    "Rapid diagnostic microfluidic PDMS capillary channel (<15 minutes time-to-result)",
                    "Isothermal 37C RPA recombinase enzymatic reaction chamber",
                    "Smartphone optical fluorometer reader interface and disposable cartridge",
                ],
                "time_offset_hours": -1,
            },
        ],
        "run_history": {
            "prompt": "Develop microfluidic Cas13a biosensor platform for rapid optical detection of airborne viral RNA",
            "summary": "Engineered automated microfluidic Cas13a collateral cleavage assay with isothermal RPA pre-amplification. Validated sub-femtomolar viral RNA detection in 12.4 minutes on a disposable capillary microfluidics cartridge.",
            "duration_seconds": 18.4,
            "notion": {
                "hub_page_url": "https://www.notion.so/Autonomous-R-D-Runs-Hub-crispr_cas13_rna_sensor",
                "run_page_url": "https://www.notion.so/Run-Workspace-crispr_cas13_rna_sensor",
                "kanban_database_id": "8b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
            },
            "calendar_event_links": [
                {
                    "title": "Cas13a Isothermal Cleavage Assay Review",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Tomorrow at 11:30 AM IST",
                },
            ],
        },
    },
    {
        "project_key": "aerospace_hypersonic_scramjet",
        "title": "Mach 7 Scramjet Inlet Shock Isolator CFD",
        "original_goal": "Computational modeling and boundary-layer shock-wave interaction control for a Mach 7 scramjet inlet isolator using active bleed valves.",
        "invariants": {
            "hard_invariants": [
                {
                    "id": "INV-1",
                    "label": "Shock Train Stability Margin (>= 15% pressure margin before unstart)",
                    "description": "Shock train boundary layer interaction must prevent inlet unstart under combustor backpressure fluctuations up to 15%.",
                    "keywords": ["shock train", "stability margin", "unstart", "shock wave", "boundary layer", "aerodynamic"],
                },
                {
                    "id": "INV-2",
                    "label": "Total Pressure Recovery Ratio (Pt2/Pt0 >= 0.65 across isolator)",
                    "description": "Isolator duct geometry must maintain core airflow stagnation pressure recovery above 65%.",
                    "keywords": ["pressure recovery", "pt2/pt0", "isolator", "mach 7", "scramjet", "pressure ratio"],
                },
                {
                    "id": "INV-3",
                    "label": "Active Bleed Mass Flow Penalty (<= 3.5% core captured airflow)",
                    "description": "Total bleed flow diverted through active boundary layer suction cavity must remain below 3.5% of inlet mass flow.",
                    "keywords": ["bleed", "mass flow", "bleed valves", "suction cavity", "porous", "bleed flow"],
                },
            ],
            "soft_scope": [
                {
                    "id": "SCOPE-1",
                    "label": "High-frequency Piezoelectric Flap Actuators",
                    "description": "Fast piezoelectric micro-valves for active shock oscillations damping at 2 kHz.",
                    "keywords": ["piezoelectric", "actuator", "flap", "piezo-valve"],
                },
                {
                    "id": "SCOPE-2",
                    "label": "FPGA Real-time Shock Position Kalman Filter",
                    "description": "Sub-millisecond shock front tracking estimator mapped into Xilinx Ultrascale+ FPGA.",
                    "keywords": ["fpga", "kalman filter", "shock position", "closed-loop", "vhdl"],
                },
            ],
        },
        "sessions": [
            {
                "session_number": 1,
                "change_type": "BASELINE",
                "alignment_score": 100.0,
                "old_goal_summary": "",
                "new_goal_summary": "Anchored Mach 7 scramjet inlet isolator shock train control specification.",
                "reason": "Baseline aerodynamic geometry and shock stability invariant contracts anchored.",
                "task_titles": [
                    "Mach 7 RANS Shock Train Simulation",
                    "Isolator Pressure Ratio Boundary Map",
                    "Boundary Layer Bleed Geometry Spec",
                    "Unstart Prevention Envelope Analysis",
                ],
                "time_offset_hours": -7,
            },
            {
                "session_number": 2,
                "change_type": "DRIFT",
                "alignment_score": 41.2,
                "old_goal_summary": "Mach 7 scramjet inlet isolator CFD",
                "new_goal_summary": "Low-pressure turbofan compressor stator and subsonic blade flutter aeroelasticity.",
                "reason": "Severe Scope Drift: Focus wandered from Mach 7 hypersonic shock boundary layer into subsonic turbojet blade aeroelasticity.",
                "task_titles": [
                    "Low-pressure Turbofan Compressor Stator",
                    "Subsonic Blade Flutter Aeroelasticity",
                    "Titanium Alloy Casting Schedule",
                ],
                "time_offset_hours": -5,
            },
            {
                "session_number": 3,
                "change_type": "REANCHOR",
                "alignment_score": 87.8,
                "old_goal_summary": "Low-pressure turbofan compressor stator",
                "new_goal_summary": "Re-anchored: Micro-vortex generator array with adaptive porous bleed cavity.",
                "reason": "Contract Re-anchored: Recalibrated shock train control using passive vortex generators + adaptive bleed, preventing isolator unstart.",
                "task_titles": [
                    "Mach 7 shock train stability margin (>= 15%) unstart prevention CFD",
                    "Isolator duct total pressure recovery Pt2/Pt0 (>= 0.65) boundary layer flow",
                    "Adaptive porous wall suction cavity bleed mass flow penalty (<3.5%)",
                    "Micro-vortex generator array layout and Kulite sensor telemetry",
                ],
                "time_offset_hours": -3,
            },
            {
                "session_number": 4,
                "change_type": "INTENTIONAL",
                "alignment_score": 94.6,
                "old_goal_summary": "Micro-vortex generator array with adaptive porous bleed cavity",
                "new_goal_summary": "Integrated real-time FPGA shock-position Kalman filter with piezo-valves.",
                "reason": "Approved Scope Evolution: Integrated active FPGA shock-position sensing into the isolator control envelope.",
                "task_titles": [
                    "Real-time shock position Kalman filter in VHDL on FPGA",
                    "High-frequency piezoelectric flap actuator wind tunnel bench test",
                    "Mach 7 scramjet isolator shock train stability margin validation",
                    "Active bleed mass flow optimization and total pressure recovery",
                ],
                "time_offset_hours": -1,
            },
        ],
        "run_history": {
            "prompt": "Computational modeling and boundary-layer shock-wave interaction control for Mach 7 scramjet inlet isolator",
            "summary": "Completed high-fidelity Navier-Stokes CFD simulations of Mach 7 scramjet inlet shock train. Validated micro-vortex generator array with 2.8% bleed flow ratio, sustaining a 19.4% stability margin against engine unstart.",
            "duration_seconds": 23.4,
            "notion": {
                "hub_page_url": "https://www.notion.so/Autonomous-R-D-Runs-Hub-aerospace_hypersonic_scramjet",
                "run_page_url": "https://www.notion.so/Run-Workspace-aerospace_hypersonic_scramjet",
                "kanban_database_id": "7c3d4e5f-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
            },
            "calendar_event_links": [
                {
                    "title": "Shock Boundary Layer Interaction & Unstart Review",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Tomorrow at 3:00 PM IST",
                },
            ],
        },
    },
    {
        "project_key": "solid_state_battery_electrolyte",
        "title": "LLZO Solid-State Electrolyte Dendrite Suppression",
        "original_goal": "High-throughput DFT screening of garnet-type LLZO solid-state electrolytes with Al/Nb co-doping to prevent lithium dendrite penetration at >5 mA/cm².",
        "invariants": {
            "hard_invariants": [
                {
                    "id": "INV-1",
                    "label": "Room-Temperature Ionic Conductivity (>= 1.0 mS/cm at 25C)",
                    "description": "Bulk and grain boundary lithium-ion conductivity of cubic LLZO garnet phase must exceed 1.0 mS/cm.",
                    "keywords": ["ionic conductivity", "conductivity", "ms/cm", "llzo", "lithium ion", "hopping energy"],
                },
                {
                    "id": "INV-2",
                    "label": "Critical Current Density for Dendrite Suppression (CCD >= 5.0 mA/cm²)",
                    "description": "Solid electrolyte pellet must withstand lithium stripping/plating without short-circuit dendrite penetration up to 5 mA/cm².",
                    "keywords": ["critical current density", "ccd", "dendrite", "ma/cm²", "lithium metal", "grain boundary"],
                },
                {
                    "id": "INV-3",
                    "label": "Electrochemical Stability Window (0 to 4.5V vs Li/Li+)",
                    "description": "Phase decomposition enthalpy must remain stable against reduction at 0V (anode) and oxidation up to 4.5V (cathode).",
                    "keywords": ["electrochemical stability", "stability window", "4.5v", "garnet", "electrolyte", "decomposition"],
                },
            ],
            "soft_scope": [
                {
                    "id": "SCOPE-1",
                    "label": "Atomic Layer Deposition (ALD) Interlayer Wetting",
                    "description": "Ultra-thin 5nm ZnO or Al2O3 conformal coating to eliminate contact voids at the Li/LLZO interface.",
                    "keywords": ["atomic layer deposition", "ald", "zno", "wetting layer", "interlayer"],
                },
                {
                    "id": "SCOPE-2",
                    "label": "Low-temperature Sintering Flux Additives",
                    "description": "Li3BO3 flux addition to reduce garnet sintering temperature below 1050°C while achieving >96% relative density.",
                    "keywords": ["sintering", "flux additive", "grain boundary", "density"],
                },
            ],
        },
        "sessions": [
            {
                "session_number": 1,
                "change_type": "BASELINE",
                "alignment_score": 100.0,
                "old_goal_summary": "",
                "new_goal_summary": "Anchored cubic LLZO solid-state electrolyte DFT screening targets.",
                "reason": "Baseline garnet crystal structure and transport invariant contracts anchored.",
                "task_titles": [
                    "Li7La3Zr2O12 Cubic Phase DFT Relaxation",
                    "Lithium Ion Hopping Energy Barrier Calculation",
                    "Grain Boundary Shear Modulus Analysis",
                    "Electrochemical Window Screening",
                ],
                "time_offset_hours": -6,
            },
            {
                "session_number": 2,
                "change_type": "DRIFT",
                "alignment_score": 37.5,
                "old_goal_summary": "Cubic LLZO solid-state electrolyte DFT screening",
                "new_goal_summary": "Liquid flammable organic carbonates (EC/DMC) with LiPF6 salt formulation.",
                "reason": "Critical Drift: Drifted back to conventional liquid organic electrolyte systems, abandoning the solid-state safety envelope.",
                "task_titles": [
                    "LiPF6 in EC/DMC Electrolyte Conductivity",
                    "Flammability Flash-Point Measurement",
                    "Polyethylene Separator Porosity",
                ],
                "time_offset_hours": -4,
            },
            {
                "session_number": 3,
                "change_type": "REANCHOR",
                "alignment_score": 90.2,
                "old_goal_summary": "Liquid flammable organic carbonates (EC/DMC)",
                "new_goal_summary": "Re-anchored: Al/Ta co-doped LLZO garnet with 5nm ALD ZnO wetting interlayer.",
                "reason": "Contract Re-anchored: Introduced 5nm ALD ZnO interlayer on LLZO pellet, eliminating Li wetting void formation and suppressing dendrites.",
                "task_titles": [
                    "Cubic LLZO garnet room-temperature ionic conductivity (>1.0 mS/cm) DFT",
                    "Critical Current Density (CCD >= 5.0 mA/cm²) dendrite suppression modeling",
                    "Electrochemical stability window (0 to 4.5V vs Li/Li+) decomposition screening",
                    "5nm Atomic Layer Deposition (ALD) ZnO wetting interlayer on Li metal",
                ],
                "time_offset_hours": -1.5,
            },
        ],
        "run_history": {
            "prompt": "DFT screening of garnet-type LLZO solid-state electrolytes with Al/Nb co-doping to prevent lithium dendrite penetration",
            "summary": "Screened 48 cubic garnet LLZO compositions via DFT and molecular dynamics. Identified Al0.25Li6.25La3Zr1.75Ta0.25O12 as optimal candidate, achieving 1.34 mS/cm conductivity and >6.2 mA/cm² critical current density.",
            "duration_seconds": 20.1,
            "notion": {
                "hub_page_url": "https://www.notion.so/Autonomous-R-D-Runs-Hub-solid_state_battery_electrolyte",
                "run_page_url": "https://www.notion.so/Run-Workspace-solid_state_battery_electrolyte",
                "kanban_database_id": "6d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f8a",
            },
            "calendar_event_links": [
                {
                    "title": "LLZO Solid Electrolyte Interlayer Review",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Tomorrow at 4:30 PM IST",
                },
            ],
        },
    },
    {
        "project_key": "gan_rf_amplifier_5g",
        "title": "28 GHz GaN Doherty Power Amplifier (5G mmWave)",
        "original_goal": "Design a 28 GHz GaN-on-SiC Doherty power amplifier delivering >40% power-added efficiency (PAE) with >33 dBm saturated output power for 5G mmWave.",
        "invariants": {
            "hard_invariants": [
                {
                    "id": "INV-1",
                    "label": "Power-Added Efficiency at 6 dB Back-Off (PAE >= 40%)",
                    "description": "Asymmetrical Doherty architecture must sustain PAE >= 40% at 6 dB power back-off under complex modulated 5G NR signals.",
                    "keywords": ["power-added efficiency", "pae", "back-off", "doherty", "efficiency", "modulation"],
                },
                {
                    "id": "INV-2",
                    "label": "Saturated Output Power (Psat >= 33 dBm at 28 GHz)",
                    "description": "Carrier and peaking amplifier combined output power must exceed 33 dBm across the 27.5 to 28.35 GHz band.",
                    "keywords": ["psat", "saturated output power", "33 dbm", "28 ghz", "mmwave", "gan", "output power"],
                },
                {
                    "id": "INV-3",
                    "label": "Peak Channel Junction Temperature (Tj <= 175C under CW RF)",
                    "description": "Through-substrate thermal via array on 100um SiC substrate must limit maximum channel temperature to 175°C.",
                    "keywords": ["junction temperature", "thermal via", "tj", "heat dissipation", "sic substrate", "thermal fem"],
                },
            ],
            "soft_scope": [
                {
                    "id": "SCOPE-1",
                    "label": "Integrated On-Chip Envelope Tracking Diode",
                    "description": "On-chip Schottky diode envelope detector for fast adaptive gate bias modulation and AM-PM linearization.",
                    "keywords": ["envelope detector", "schottky", "envelope tracking", "am-pm"],
                },
                {
                    "id": "SCOPE-2",
                    "label": "Compact QFN Surface-Mount Package Transition",
                    "description": "Electromagnetic co-simulation of wirebond parasitics into low-loss plastic QFN package.",
                    "keywords": ["qfn", "package", "wirebond", "mmic pad"],
                },
            ],
        },
        "sessions": [
            {
                "session_number": 1,
                "change_type": "BASELINE",
                "alignment_score": 100.0,
                "old_goal_summary": "",
                "new_goal_summary": "Anchored 28 GHz GaN-on-SiC Doherty power amplifier specification.",
                "reason": "Baseline RF semiconductor MMIC parameters and thermal dissipation invariants anchored.",
                "task_titles": [
                    "0.15um GaN-on-SiC Large-Signal Model",
                    "Quarter-wave Doherty Inverter Topology",
                    "Thermal Via Array Heat Dissipation Design",
                    "Input Matching Network Simulation",
                ],
                "time_offset_hours": -8,
            },
            {
                "session_number": 2,
                "change_type": "DRIFT",
                "alignment_score": 43.1,
                "old_goal_summary": "28 GHz GaN-on-SiC Doherty power amplifier",
                "new_goal_summary": "2.4 GHz Class-AB CMOS power amplifier and low-voltage on-chip biasing.",
                "reason": "Domain Drift: Downshifted from 28 GHz mmWave GaN to 2.4 GHz silicon CMOS, collapsing power density and frequency goals.",
                "task_titles": [
                    "2.4 GHz Class-AB CMOS Power Amp",
                    "On-chip Inductor Q-Factor Analysis",
                    "Low-voltage 1.8V biasing circuit",
                ],
                "time_offset_hours": -5,
            },
            {
                "session_number": 3,
                "change_type": "REANCHOR",
                "alignment_score": 91.8,
                "old_goal_summary": "2.4 GHz Class-AB CMOS power amplifier",
                "new_goal_summary": "Re-anchored: Asymmetrical GaN Doherty topology with harmonic termination resonator.",
                "reason": "Contract Re-anchored: Restored mmWave GaN design; asymmetrical Doherty delivers 42.8% PAE at 6 dB back-off.",
                "task_titles": [
                    "Asymmetrical 28 GHz GaN Doherty power amplifier (Psat >= 33 dBm)",
                    "Second harmonic trapping for power-added efficiency (PAE >= 40% at 6 dB back-off)",
                    "Through-substrate thermal via array heat dissipation (Tj <= 175C)",
                    "Input matching network and stability verification",
                ],
                "time_offset_hours": -2.5,
            },
            {
                "session_number": 4,
                "change_type": "INTENTIONAL",
                "alignment_score": 96.7,
                "old_goal_summary": "Asymmetrical GaN Doherty topology with harmonic termination",
                "new_goal_summary": "Integrated on-chip Schottky envelope detector for AM-PM distortion linearization.",
                "reason": "Approved Scope Evolution: Added on-chip envelope tracking interface to facilitate real-time DPD correction without violating thermal envelope.",
                "task_titles": [
                    "On-chip Schottky diode envelope detector subcircuit (SCOPE-1)",
                    "Asymmetrical 28 GHz GaN Doherty power amplifier (Psat >= 33 dBm)",
                    "Second harmonic trapping for power-added efficiency (PAE >= 40%)",
                    "Thermal via array heat dissipation (Tj <= 175C) on SiC substrate",
                ],
                "time_offset_hours": -0.8,
            },
        ],
        "run_history": {
            "prompt": "Design 28 GHz GaN-on-SiC Doherty power amplifier delivering >40% PAE with >33 dBm Psat for 5G mmWave",
            "summary": "Synthesized asymmetrical 28 GHz GaN MMIC Doherty power amplifier. Achieved 42.8% PAE at 6 dB back-off, 34.2 dBm Psat, and maximum junction temperature of 152°C on 100um SiC substrate.",
            "duration_seconds": 22.3,
            "notion": {
                "hub_page_url": "https://www.notion.so/Autonomous-R-D-Runs-Hub-gan_rf_amplifier_5g",
                "run_page_url": "https://www.notion.so/Run-Workspace-gan_rf_amplifier_5g",
                "kanban_database_id": "5e6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c",
            },
            "calendar_event_links": [
                {
                    "title": "28 GHz GaN Doherty MMIC Design Review",
                    "url": "https://calendar.google.com/calendar/u/0/r/eventedit",
                    "time": "Tomorrow at 5:00 PM IST",
                },
            ],
        },
    },
]


def seed_firestore():
    print("🚀 Starting Firestore Seeding for 5 Showcase Projects...")
    if not db:
        print("❌ Error: Firestore db is not initialized!")
        sys.exit(1)

    now = datetime.now()

    for proj in SHOWCASE_PROJECTS:
        pk = proj["project_key"]
        print(f"\n📦 Seeding Project: {pk} ({proj['title']})...")

        # 1. Clean existing logs for this project key to prevent duplicate accumulations
        try:
            old_logs = list(
                db.collection("goal_evolution_log")
                .where(filter=FieldFilter("project_key", "==", pk))
                .stream()
            )
            for d in old_logs:
                d.reference.delete()
            print(f"   🧹 Purged {len(old_logs)} previous evolution logs for {pk}")
        except Exception as e:
            print(f"   ⚠️ Log purge notice: {e}")

        # Clean old run_history docs for this project key
        try:
            old_runs = list(
                db.collection("run_history")
                .where(filter=FieldFilter("project_key", "==", pk))
                .stream()
            )
            for d in old_runs:
                d.reference.delete()
            print(f"   🧹 Purged {len(old_runs)} previous run_history records for {pk}")
        except Exception as e:
            print(f"   ⚠️ Run history purge notice: {e}")

        # 2. Compute authentic baseline embedding and hash
        embedding = _get_embedding(proj["original_goal"])
        version = _goal_version_hash(embedding)

        # 3. Store goal_state
        goal_state_data = {
            "project_key": pk,
            "original_goal": proj["original_goal"],
            "baseline_embedding": embedding,
            "goal_version": version,
            "invariants": proj["invariants"],
            "created_at": (now - timedelta(hours=12)).isoformat(),
            "updated_at": now.isoformat(),
        }
        db.collection("goal_state").document(pk).set(goal_state_data)
        print(f"   🎯 Anchored goal_state (Version: {version})")

        # 4. Insert Evolution Log Sessions
        for s in proj["sessions"]:
            s_time = (now + timedelta(hours=s["time_offset_hours"])).isoformat()
            log_doc = {
                "project_key": pk,
                "session_number": s["session_number"],
                "change_type": s["change_type"],
                "alignment_score": s["alignment_score"],
                "old_goal_summary": s["old_goal_summary"],
                "new_goal_summary": s["new_goal_summary"],
                "reason": s["reason"],
                "task_titles": s["task_titles"],
                "timestamp": s_time,
            }
            db.collection("goal_evolution_log").document().set(log_doc)
            print(f"      ↳ Session {s['session_number']} ({s['change_type']}): {s['alignment_score']}%")

        # 5. Insert Run History entry
        rh = proj["run_history"]
        run_snapshot = {
            "status": "success",
            "prompt": rh["prompt"],
            "project_key": pk,
            "duration_seconds": rh["duration_seconds"],
            "notion": rh["notion"],
            "calendar_event_links": rh["calendar_event_links"],
            "goal_tracking": {
                "alignment_score": proj["sessions"][-1]["alignment_score"],
                "change_type": proj["sessions"][-1]["change_type"],
                "session_number": len(proj["sessions"]),
                "gate_triggered": False,
            },
            "outcome": {
                "summary": rh["summary"],
                "project_key": pk,
            },
        }

        run_doc = {
            "timestamp": (now + timedelta(hours=proj["sessions"][-1]["time_offset_hours"])).isoformat(),
            "prompt": rh["prompt"],
            "summary": rh["summary"],
            "project_key": pk,
            "result_snapshot": run_snapshot,
        }
        db.collection("run_history").document().set(run_doc)
        print(f"   📊 Inserted run_history record for sidebar past runs.")

    print("\n✨ Seeding completed successfully! 5 projects are now populated in Firestore.")


if __name__ == "__main__":
    seed_firestore()
