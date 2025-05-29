import asyncio 
import os 
from dataclasses import dataclass 
from typing import List, Dict, Any 
from pathlib import Path 

from agents import Agent, function_tool, RunContextWrapper, Runner 

@dataclass 
class CodingContext:
    """Context for coding operations"""
    project_path: str 
    current_path: str 
    tasks: Dict[str, Any]

# File Operations Tools
@function_tool 
async def read_file(ctx: RunContextWrapper[CodingContext], filepath: str) -> str:
    """Read contents of a file"""
    full_path = Path(ctx.context.project_path) / filepath
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
@function_tool 
async def write_file(ctx: RunContextWrapper[CodingContext], filepath: str, content: str) -> str:
    """write content to a file"""
    full_path = Path(ctx.context.project_path) / filepath 
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@function_tool
async def list_files(ctx: RunContextWrapper[CodingContext], directory: str =".") -> str:
    """List files in a directory"""
    full_path = Path(ctx.context.project_path) / directory 
    try:
        files = [] 
        for item in full_path.rglob("*"):
            if item.is_file() and not any(part.startswith('.') for part in item.parts):
                files.append(str(item.relative_to(full_path.parent)))
        return "\n".join(files[:50])
    except Exception as e:
        return f"Error listing files: {str(e)}"

@function_tool
async def run_command(ctx: RunContextWrapper[CodingContext], command: str) -> str:
    """Execute a shell command"""
    try:
        import subprocess 
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=ctx.context.project_path,
            timeout=30
        )
        output = result.stdout + result.stderr 
        return f"Command: {command}\nOutput: {output}"
    except Exception as e:
        return f"Error running command: {str(e)}"
    
@function_tool
async def create_git_branch(ctx: RunContextWrapper[CodingContext], branch_name: str) -> str:
    """Create and checkout a new git branch"""
    try:
        import subprocess
        subprocess.run(["git", "checkout", "-b", branch_name],
                       cwd=ctx.context.project_path, check=True)
        ctx.context.current_branch = branch_name 
        return f"Created and switched to branch: {branch_name}"
    except Exception as e:
        return f"Error creating branch: {str(e)}"
    
class AgenticCodingSystem:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.context = CodingContext(
            project_path=project_path,
            current_branch="main",
            tasks={} 
        )

        # Common tools for all agents 
        self.common_tools = [
            read_file, write_file, list_files, run_command, create_git_branch
        ] 

        # Code Analysis Agent 
        self.analyzer_agent = Agent(
            name="CodeAnalyzer",
            instructions="""You are a code analysis expert. Your job is to:
            1. Understand codebases by reading files and analyzing structure
            2. Identify bugs, code quality issues, and improvement opportunities  
            3. Explain how codebases work and their organization
            4. Always read multiple files to understand context before making conclusions
            
            When analyzing code:
            - Start by listing files to understand structure
            - Read key files like README, main modules, config files
            - Look for patterns, architecture, and dependencies
            - Provide clear, actionable insights""",
            tools=self.common_tools,
            handoff_description="Analyzes codebases, finds bugs, explains code organization"
        )
        
        # Code Generation Agent  
        self.generator_agent = Agent(
            name="CodeGenerator",
            instructions="""You are a code generation expert. Your job is to:
            1. Write new code based on specifications
            2. Fix bugs and implement features
            3. Create tests and documentation
            4. Follow existing code patterns and best practices
            
            When writing code:
            - Always read existing code first to understand patterns
            - Create new git branches for changes
            - Write clean, well-documented code
            - Include error handling and edge cases
            - Run tests after making changes""",
            tools=self.common_tools,
            handoff_description="Generates new code, fixes bugs, implements features"
        )
        
        # Planning Agent
        self.planner_agent = Agent(
            name="EngineeringPlanner", 
            instructions="""You are an engineering planning expert. Your job is to:
            1. Create detailed engineering plans and specifications
            2. Break down complex tasks into smaller steps
            3. Design system architecture and workflows
            4. Create project roadmaps and documentation
            
            When planning:
            - Analyze the existing codebase first
            - Identify requirements and constraints  
            - Create step-by-step implementation plans
            - Consider testing, deployment, and maintenance
            - Write plans in clear markdown format""",
            tools=self.common_tools,
            handoff_description="Creates engineering plans, specs, and project roadmaps"
        )
        
        # Test Generation Agent
        self.tester_agent = Agent(
            name="TestGenerator",
            instructions="""You are a test generation expert. Your job is to:
            1. Design comprehensive testing strategies
            2. Write unit tests, integration tests, and validation scripts
            3. Create test automation workflows
            4. Ensure code quality and coverage
            
            When creating tests:
            - Analyze existing code to understand what to test
            - Write tests that cover edge cases and error conditions
            - Use appropriate testing frameworks for the language
            - Create test data and fixtures as needed
            - Document testing procedures""",
            tools=self.common_tools, 
            handoff_description="Creates tests, testing strategies, and quality assurance"
        )

    async def run_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Run multple coding tasks in parellel."""
        async def run_single_task(task):
            agent_name = task.get("agent", "analyzer")
            prompt = task.get("prompt", "")

            # Select appropriate agent 
            agent_map = {
                "analyzer": self.analyzer_agent, 
                "generator": self.generator_agent,
                "planner": self.planner_agent,
                "tester": self.tester_agent
            }

            agent = agent_map.get(agent_name, self.analyzer_agent)

            # Run the task 
            result = await Runner.run(
                starting_agent=agent,
                input=prompt,
                context=self.context 
            )

            return {
                "task": task,
                "result": result.final_output,
                "agent": agent_name
            }
        
    async def analyze_codebase(self) -> str:
        """Analyze the codebase structure and purpose"""
        result = await Runner.run(
            starting_agent=self.analyzer_agent,
            input="Analyze this codebase. HHow is it organized? What does it do? What's its purpose?",
            context=self.context 
        )
        return result.final_output 
    
    async def find_and_fix_bug(self) -> str:
        """Find a bug and create a fix"""
        result = await Runner.run(
            starting_agent=self.analyzer_agent,
            input="Find a bug in this codebase and write a fix for it. Create a new branch and implement the fix.",
            context=self.context 
        )
        return result.final_output 
    
    async def create_engineering_plan(self) -> str:
        """Create an engineering plan aligned with codebase purpose"""
        result = await Runner.run(
            starting_agent=self.planner_agent,
            input="Create a new engineering plan that aligns with this codebase's purpose. Create a new markdown file with the plan.",
            context=self.context
        )
        return result.final_output

    async def design_testing_system(self) -> str:
        """Design a testing system for the codebase"""
        result = await Runner.run(
            starting_agent=self.tester_agent,
            input="Design a testing system for this codebase that can validate arbitrary engineering tasks are completed correctly.",
            context=self.context
        )
        return result.final_output
    
async def main():

    coding_system = AgenticCodingSystem(r"C:\Users\sidki\source\repos\ukfv4")
    print(await coding_system.analyze_codebase())

if __name__ == "__main__":
    asyncio.run(main())     


    # Define parallel tasks
            