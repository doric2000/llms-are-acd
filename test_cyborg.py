print("Testing a basic CybORG import...")

try:
    from CybORG import CybORG
    from CybORG.Agents.SimpleAgents import EnterpriseGreenAgent
    from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
    
    print("CybORG imports worked successfully!")
    print("Installation successful!")
    exit(0)
except Exception as e:
    print(f"\n Test failed: {e}")
    exit(1)
