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
        url = f"{self.base_url}/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        log.info(f"Requesting tools information from MCP server at {url}")
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                log.error(f"MCP Error listing tools: {result['error']}")
                return []
            
            if "result" in result and "tools" in result["result"]:
                return result["result"]["tools"]
            
            log.warning(f"Unexpected response format: {result}")
            return []
            
        except Exception as e:
            log.error(f"Error listing tools: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a specific tool from the MCP server using HTTP/JSON-RPC (no session_id required).
        
        Args:
            tool_name (str): Name of the tool to be called
            arguments (Dict[str, Any]): Arguments for the tool
            
        Returns:
            Dict[str, Any]: Result of the tool execution
        """
        url = f"{self.base_url}/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        log.info(f"Calling tool {tool_name} at {url}")
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Handle error responses
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown MCP error")
                log.error(f"MCP Error calling tool {tool_name}: {error_msg}")
                raise Exception(f"MCP tool call failed: {error_msg}")
                
            # Extract content from result
            if "result" in result:
                tool_result = result["result"]
                if "content" in tool_result and tool_result["content"]:
                    # Return the text content from the first content item
                    return {"content": tool_result["content"][0]["text"]}
                else:
                    return tool_result
            
            log.warning(f"Unexpected response format from MCP: {result}")
            return {}
            
        except requests.exceptions.RequestException as e:
            log.error(f"Request error calling tool {tool_name}: {e}")
            raise
        except Exception as e:
            log.error(f"Error calling tool {tool_name}: {e}")
            raise
    
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