# bridge.py
# This file defines the AgentBridge class, which facilitates communication
# between different agents. It acts as a central hub or a switchboard.

class AgentBridge:
    """
    A simple bridge for agent-to-agent (A2A) communication.
    """
    def __init__(self):
        """
        Initializes the bridge with an empty dictionary to store registered agents.
        """
        self._agents = {}
        print("[Bridge] Agent Communication Bridge initialized.")

    def register_agent(self, name: str, agent_instance):
        """
        Registers an agent instance with a given name.
        """
        self._agents[name] = agent_instance
        print(f"[Bridge] Agent '{name}' has been registered.")

    def request(self, target_agent_name: str, task: str, data: dict) -> str:
        """
        Sends a request from one agent to another.
        """
        print(f"[Bridge] Routing request to '{target_agent_name}' for task '{task}'.")
        if target_agent_name in self._agents:
            target_agent = self._agents[target_agent_name]
            if hasattr(target_agent, 'handle_request'):
                # This calls the specific handler method on the target agent
                return target_agent.handle_request(task, data)
            else:
                return f"Error: Agent '{target_agent_name}' cannot handle requests."
        else:
            return f"Error: Agent '{target_agent_name}' not found."
