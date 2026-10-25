"""
Verification test suite for Phase 2: Agent integration & research_tool fix
"""

import sys

def test_phase_2():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE 2: agents.py & research_tool.py")
    print("=" * 60)

    # 1. Test agents.py import
    try:
        from agents import tech_lead_agent, research_agent, scrum_master_agent, workspace_prep_agent
        print("✅ Step 1: agents.py imported successfully without circular import")
    except Exception as e:
        print(f"❌ Failed to import agents: {e}")
        sys.exit(1)

    # 2. Verify tech_lead_agent tools
    tool_names = [getattr(t, "__name__", str(t)) for t in tech_lead_agent.tools]
    print(f"Tech Lead tools count: {len(tech_lead_agent.tools)} ({tool_names})")
    assert "save_goal_state" in tool_names, "save_goal_state not in tech_lead_agent.tools"
    assert "goal_health_check" in tool_names, "goal_health_check not in tech_lead_agent.tools"
    print("✅ Step 2: save_goal_state and goal_health_check verified in tech_lead_agent.tools")

    # 3. Verify subagents intact
    sub_agent_names = [getattr(sa, "name", str(sa)) for sa in tech_lead_agent.sub_agents]
    assert "research_agent" in sub_agent_names
    assert "scrum_master_agent" in sub_agent_names
    assert "workspace_prep_agent" in sub_agent_names
    print(f"✅ Step 3: Subagents intact: {sub_agent_names}")

    # 4. Verify tech_lead_agent instructions
    assert "GOAL TRACKING" in tech_lead_agent.instruction
    assert "Workflow order:" in tech_lead_agent.instruction
    assert "0. goal tracking" in tech_lead_agent.instruction
    print("✅ Step 4: Tech Lead instructions updated with goal tracking workflow")

    # 5. Verify research_tool.py line 198 fix
    import research_tool
    import inspect
    src = inspect.getsource(research_tool.search_arxiv)
    assert "lines.append(f\"{resultIndex}. **{title}**\")" in src, "resultIndex fix missing from search_arxiv!"
    print("✅ Step 5: research_tool.py search_arxiv resultIndex fix verified")

    print("\n🎉 ALL PHASE 2 VERIFICATION CHECKS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_phase_2()
