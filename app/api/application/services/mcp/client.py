from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MCPClientInterface(ABC):
    """
    Interface for MCP client that defines the contract for interacting with MCP server.
    """

    @abstractmethod
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lists all available tools from the MCP server.
        
        Returns:
            List[Dict[str, Any]]: List of available tools
        """
        pass
    
    @abstractmethod
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a specific tool from the MCP server.
        
        Args:
            tool_name (str): Name of the tool to be called
            arguments (Dict[str, Any]): Arguments for the tool
            
        Returns:
            Dict[str, Any]: Result of the tool execution
        """
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Sends a generic message to the MCP server.
        
        Args:
            message (str): Message to be sent
            
        Returns:
            Dict[str, Any]: Response from the server
        """
        pass
