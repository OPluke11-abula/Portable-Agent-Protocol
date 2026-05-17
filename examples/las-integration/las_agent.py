"""
LAS (Lightweight Agent System) + PAP (Portable Agent Protocol) Integration Example

This script demonstrates how a LAS-based agent uses the PAP `AgentEngine` to 
bootstrap its persona, memory, and tool routing from the standardized `.agent/` directory.

NOTE: This is a conceptual demonstration. `las_framework` is a mock import representing 
the hypothetical LAS library.
"""

import sys
from pathlib import Path

# Mock import for the LAS framework
try:
    from las_framework import Agent, MessageBus
except ImportError:
    print("This is a structural demonstration. `las_framework` is not a real package.")

# Import the PAP AgentEngine
# Assuming this script is run from within the repository
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent_runtime import AgentEngine


class LasPapAgent:
    def __init__(self, workspace_path: str = ".agent/agent.md"):
        # 1. Initialize PAP Engine (Parses Schema, Validates Layout)
        self.engine = AgentEngine(workspace_path)
        
        # 2. Extract configuration for LAS
        agent_name = self.engine.config.get("name", "UnnamedAgent")
        
        # Read the persona document directly using the engine's layout resolver
        persona_path = self.engine.layout.get("root") / "persona.md"
        persona_prompt = persona_path.read_text(encoding="utf-8") if persona_path.exists() else ""
        
        # 3. Instantiate the LAS Agent
        # We pass the persona prompt from PAP directly into LAS
        self.las_agent = Agent(
            name=agent_name,
            system_prompt=persona_prompt
        )
        
        # 4. Bind PAP tools to LAS tool handler
        # When LAS decides to call a tool, we route it through the PAP Engine
        self.las_agent.on_tool_call(self._handle_tool_call)

    def _handle_tool_call(self, tool_name: str, params: dict) -> dict:
        """Route tool calls from LAS to the PAP Router/MCP Bridge."""
        print(f"[LAS-PAP Bridge] Routing tool '{tool_name}' via PAP Engine...")
        
        # Example of persisting state before executing tool
        self.engine.memory.write(f"last_tool_call", tool_name)
        
        try:
            # The PAP engine handles execution (either local functions or via MCP bridge)
            result = self.engine.run(tool_name, params)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start(self):
        """Start the LAS execution loop."""
        print(f"Starting {self.las_agent.name} with PAP backend...")
        # self.las_agent.run() 
        print("Initialization and routing bindings successful!")


if __name__ == "__main__":
    # Bootstrap the agent using the local .agent/ workspace
    app = LasPapAgent(".agent/agent.md")
    app.start()
