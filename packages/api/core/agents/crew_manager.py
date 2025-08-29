from crewai import Agent, Task, Crew, Process
from typing import List, Dict
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NEURA.CrewManager")

class AgentRole:
    """Predefined agent roles with specific capabilities"""
    
    RESEARCHER = {
        "name": "Research Specialist",
        "goal": "Find and analyze information from various sources",
        "backstory": "Expert at gathering and analyzing information from multiple sources"
    }
    
    WRITER = {
        "name": "Content Creator",
        "goal": "Create high-quality content based on research",
        "backstory": "Experienced content creator with expertise in various formats"
    }
    
    DEVELOPER = {
        "name": "Code Specialist",
        "goal": "Develop and optimize code solutions",
        "backstory": "Senior developer with full-stack expertise"
    }
    
    ANALYST = {
        "name": "Data Analyst",
        "goal": "Analyze data and provide insights",
        "backstory": "Expert in data analysis and visualization"
    }

class CrewManager:
    """Manages AI agent crews and their tasks"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.crews: Dict[str, Crew] = {}
        self.tasks: Dict[str, Task] = {}
        
    def create_agent(self, role_config: Dict, agent_id: str = None) -> Agent:
        """Create a new agent with specified role"""
        try:
            agent = Agent(
                name=role_config["name"],
                goal=role_config["goal"],
                backstory=role_config["backstory"],
                allow_delegation=True,
                verbose=True
            )
            
            if agent_id:
                self.agents[agent_id] = agent
                
            logger.info(f"Created agent: {role_config['name']}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
            
    def create_task(self, 
                    task_id: str,
                    description: str,
                    agent: Agent,
                    context: Dict = None) -> Task:
        """Create a new task for an agent"""
        try:
            task = Task(
                description=description,
                agent=agent,
                context=context or {}
            )
            
            self.tasks[task_id] = task
            logger.info(f"Created task: {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
            
    def create_crew(self, 
                    crew_id: str,
                    agents: List[Agent],
                    tasks: List[Task],
                    process: Process = Process.sequential) -> Crew:
        """Create a new crew with specified agents and tasks"""
        try:
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=process,
                verbose=True
            )
            
            self.crews[crew_id] = crew
            logger.info(f"Created crew: {crew_id}")
            return crew
            
        except Exception as e:
            logger.error(f"Error creating crew: {str(e)}")
            raise
            
    def execute_crew(self, crew_id: str) -> Dict:
        """Execute tasks for a specific crew"""
        try:
            crew = self.crews.get(crew_id)
            if not crew:
                raise ValueError(f"Crew not found: {crew_id}")
                
            logger.info(f"Executing crew: {crew_id}")
            result = crew.kickoff()
            
            return {
                "crew_id": crew_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing crew: {str(e)}")
            return {
                "crew_id": crew_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get status of a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {
                "agent_id": agent_id,
                "status": "not_found",
                "timestamp": datetime.now().isoformat()
            }
            
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
        
    def get_crew_status(self, crew_id: str) -> Dict:
        """Get status of a specific crew"""
        crew = self.crews.get(crew_id)
        if not crew:
            return {
                "crew_id": crew_id,
                "status": "not_found",
                "timestamp": datetime.now().isoformat()
            }
            
        return {
            "crew_id": crew_id,
            "agent_count": len(crew.agents),
            "task_count": len(crew.tasks),
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = CrewManager()
    
    # Create agents
    researcher = manager.create_agent(AgentRole.RESEARCHER, "researcher_1")
    writer = manager.create_agent(AgentRole.WRITER, "writer_1")
    
    # Create tasks
    research_task = manager.create_task(
        "task_1",
        "Research the latest AI trends",
        researcher
    )
    
    writing_task = manager.create_task(
        "task_2",
        "Write a blog post about AI trends",
        writer,
        {"research": "research_task_output"}
    )
    
    # Create and execute crew
    crew = manager.create_crew(
        "crew_1",
        [researcher, writer],
        [research_task, writing_task]
    )
    
    result = manager.execute_crew("crew_1")
    print(result)
