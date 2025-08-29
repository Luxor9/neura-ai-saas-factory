import logging
from typing import Dict, Any, Optional
import json
import subprocess
from datetime import datetime
import asyncio
from termgpt import TermGPT
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NEURA.VoiceCommander")

class VoiceCommander:
    """Voice command system using TermGPT"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.term_gpt = TermGPT()
        self.command_history: List[Dict] = []
        
    async def start_listening(self):
        """Start listening for voice commands"""
        logger.info("Starting voice command system...")
        
        try:
            while True:
                command = await self.term_gpt.listen()
                if command:
                    response = await self.process_command(command)
                    await self.term_gpt.speak(response)
                    
        except Exception as e:
            logger.error(f"Error in voice command system: {str(e)}")
            
    async def process_command(self, command: str) -> str:
        """Process voice command and return response"""
        try:
            # Log command
            self.command_history.append({
                "command": command,
                "timestamp": datetime.now().isoformat()
            })
            
            # Parse command intent
            if "status" in command.lower():
                return await self.get_system_status()
                
            elif "create agent" in command.lower():
                return await self.create_new_agent(command)
                
            elif "execute task" in command.lower():
                return await self.execute_task(command)
                
            elif "stop" in command.lower():
                return await self.stop_operation(command)
                
            else:
                return "Command not recognized. Please try again."
                
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return f"Error processing command: {str(e)}"
            
    async def get_system_status(self) -> str:
        """Get current system status"""
        try:
            response = requests.get(f"{self.api_url}/health")
            status = response.json()
            
            return (
                f"System status: {status['status']}. "
                f"Active services: {', '.join(status['services'].keys())}"
            )
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return "Error getting system status"
            
    async def create_new_agent(self, command: str) -> str:
        """Create a new agent based on voice command"""
        try:
            # Extract agent type from command
            agent_type = "default"
            if "researcher" in command.lower():
                agent_type = "researcher"
            elif "writer" in command.lower():
                agent_type = "writer"
            elif "developer" in command.lower():
                agent_type = "developer"
            elif "analyst" in command.lower():
                agent_type = "analyst"
                
            # Create agent via API
            response = requests.post(
                f"{self.api_url}/agents",
                json={"type": agent_type}
            )
            
            if response.status_code == 200:
                agent_id = response.json().get("agent_id")
                return f"Created new {agent_type} agent with ID {agent_id}"
            else:
                return "Failed to create agent"
                
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return "Error creating agent"
            
    async def execute_task(self, command: str) -> str:
        """Execute a task based on voice command"""
        try:
            # Extract task details from command
            task_description = command.replace("execute task", "").strip()
            
            # Create task via API
            response = requests.post(
                f"{self.api_url}/tasks",
                json={"description": task_description}
            )
            
            if response.status_code == 200:
                task_id = response.json().get("task_id")
                return f"Created task with ID {task_id}"
            else:
                return "Failed to create task"
                
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return "Error executing task"
            
    async def stop_operation(self, command: str) -> str:
        """Stop a running operation"""
        try:
            # Extract operation ID from command
            operation_id = command.replace("stop", "").strip()
            
            # Stop operation via API
            response = requests.post(
                f"{self.api_url}/operations/{operation_id}/stop"
            )
            
            if response.status_code == 200:
                return f"Stopped operation {operation_id}"
            else:
                return "Failed to stop operation"
                
        except Exception as e:
            logger.error(f"Error stopping operation: {str(e)}")
            return "Error stopping operation"
            
    def get_command_history(self) -> List[Dict]:
        """Get history of voice commands"""
        return self.command_history

# Example usage
if __name__ == "__main__":
    commander = VoiceCommander()
    
    # Start voice command system
    asyncio.run(commander.start_listening())
