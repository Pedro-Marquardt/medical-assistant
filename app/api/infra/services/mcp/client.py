from typing import Any, Dict, List
import httpx
import requests
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log

class MCPClient:
    """
    Client for interacting with the MCP server.
    """

    def __init__(self, host: str , port: str):
        self.base_url = f"http://{host}:{port}"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lists all available tools from the MCP server with complete information.
        
        Returns:
            List[Dict[str, Any]]: List of available tools with name, description and inputSchema
        """
        url = f"{self.base_url}/tools"

        log.info(f"Requesting tools information from MCP server at {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        result = response.json()
        tools = result.get("tools", [])
        
        # Tools already come in the expected format with name, description and inputSchema
        return tools
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a specific tool from the MCP server.
        
        Args:
            tool_name (str): Name of the tool to be called
            arguments (Dict[str, Any]): Arguments for the tool
            
        Returns:
            Dict[str, Any]: Result of the tool execution
        """
        url = f"{self.base_url}/messages"
        payload = {
            "jsonrpc": "2.0",
            "id": "2", 
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("result", {})
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Sends a generic message to the MCP server.
        
        Args:
            message (str): Message to be sent
            
        Returns:
            Dict[str, Any]: Response from the server
        """
        url = f"{self.base_url}/message"
        response = requests.post(url, json={"message": message})
        response.raise_for_status()
        return response.json()