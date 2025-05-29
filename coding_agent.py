"""
Programmable Agent Module

This module implements a flexible agent system with various tools for code manipulation,
file operations, git operations, and task management. It provides a programmable interface
for automating development workflows.

Key Features:
- File operations (edit, read, list, glob)
- Search operations (grep, glob pattern matching) 
- Shell command execution
- Git operations
- Parallel task execution
- Sub-task spawning

The agent can be configured with specific allowed tools and uses Google's Gemini
for intelligence.

Example:
    agent = ProgrammableAgent(allowed_tools=["edit", "read"])
    result = await agent.execute("Edit file.txt with new content")

"""

import os
import asyncio
import argparse
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunContextWrapper
import subprocess
import re
import sys 
from colorama import init, Fore, Style
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import json
from colorama import Fore
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from misc.gemini_config import setup_gemini_client, gemini_config
from agents import FunctionTool
from pathlib import Path

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('programmable_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configure Azure OpenAI at module level
# from openai import AsyncAzureOpenAI 

#         logger.info("Azure OpenAI client configured successfully for chat_completions API")
#     except Exception as e:
#         logger.error(f"Failed to configure Azure OpenAI client: {e}")
# else:
#     logger.warning("Azure OpenAI credentials not found in environment variables")

@dataclass
class AgentContext:
    """Context object for the programmable agent containing configuration and state."""
    working_directory: str
    allowed_tools: List[str]
    git_enabled: bool = True
    commit_enabled: bool = True
    executor: ThreadPoolExecutor = None
    sub_agents: Dict[str, 'ProgrammableAgent'] = None

    def __post_init__(self):
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=4)
        if self.sub_agents is None:
            self.sub_agents = {}

# Define basic tools similar to Claude Code
@function_tool
async def edit_file(wrapper: RunContextWrapper[AgentContext], path: str, content: str) -> str:
    """Edit or create a file with new content."""
    try:
        with open(os.path.join(wrapper.context.working_directory, path), 'w') as f:
            f.write(content)
        logger.info(f"Successfully edited/created file: {path}")
        return f"Successfully edited/created {path}"
    except Exception as e:
        logger.error(f"Error editing file {path}: {str(e)}")
        return f"Error editing file: {str(e)}"
    
@function_tool
async def read_file(wrapper: RunContextWrapper[AgentContext], path: str) -> str:
    """Read the contents of a file."""
    full_path = os.path.join(wrapper.context.working_directory, path)
    try:
        # Explicitly use UTF-8 encoding to handle a wider range of characters
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully read file: {path}")
        return content
    except FileNotFoundError:
        logger.error(f"Error reading file: File not found at {full_path}")
        return f"Error reading file: File not found at {path}"
    except UnicodeDecodeError as e:
        logger.error(f"Error reading file {path} due to encoding issue: {str(e)}. Attempting fallback.")
        # Optional: Add a fallback to try another encoding or read as bytes if needed
        return f"Error reading file: Encoding issue - {str(e)}" 
    except Exception as e:
        logger.error(f"Error reading file {path}: {str(e)}")
        return f"Error reading file: {str(e)}"

@function_tool
async def mkdir(wrapper: RunContextWrapper[AgentContext], path: str) -> str:
    """Create a directory, including any necessary parent directories."""
    if "mkdir" not in wrapper.context.allowed_tools:
        logger.warning("Mkdir tool not allowed in this context")
        return "Mkdir tool not allowed in this context"
    
    full_path = os.path.join(wrapper.context.working_directory, path)
    try:
        os.makedirs(full_path, exist_ok=True)
        logger.info(f"Successfully created directory (or ensured it exists): {full_path}")
        return f"Successfully created directory: {path}"
    except Exception as e:
        logger.error(f"Error creating directory {full_path}: {str(e)}")
        return f"Error creating directory: {str(e)}"

@function_tool
async def run_bash(wrapper: RunContextWrapper[AgentContext], command: str) -> str:
    """Execute a bash command."""
    if "bash" not in wrapper.context.allowed_tools:
        logger.warning("Bash tool not allowed in this context")
        return "Bash tool not allowed in this context"
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=wrapper.context.working_directory
        )
        logger.info(f"Executed bash command: {command}")
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        logger.error(f"Error running bash command {command}: {str(e)}")
        return f"Error running command: {str(e)}"

@function_tool
async def list_files(wrapper: RunContextWrapper[AgentContext], pattern: str = "*") -> str:
    """List files in the working directory."""
    try:
        import glob
        files = glob.glob(
            os.path.join(wrapper.context.working_directory, pattern)
        )
        logger.info(f"Listed files with pattern: {pattern}")
        return "\n".join(files)
    except Exception as e:
        logger.error(f"Error listing files with pattern {pattern}: {str(e)}")
        return f"Error listing files: {str(e)}"

@function_tool
async def git_operations(wrapper: RunContextWrapper[AgentContext], operation: str, args: List[str]) -> str:
    """Perform git operations."""
    if not wrapper.context.git_enabled:
        logger.warning("Git operations not enabled")
        return "Git operations not enabled"
    
    allowed_ops = ["checkout", "branch", "add", "commit", "status"]
    if operation not in allowed_ops:
        logger.warning(f"Git operation not allowed: {operation}")
        return f"Operation {operation} not allowed"
    
    try:
        cmd = ["git", operation] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=wrapper.context.working_directory
        )
        logger.info(f"Executed git operation: {operation} {' '.join(args)}")
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        logger.error(f"Error with git operation {operation}: {str(e)}")
        return f"Error with git operation: {str(e)}"

@function_tool
async def grep_files(
    wrapper: RunContextWrapper[AgentContext], 
    pattern: str, 
    path: str = ".", 
    recursive: bool = True
) -> str:
    """Search for a pattern in files using grep (original implementation)."""
    # Reverting to original grep implementation for now
    try:
        cmd = ["grep"]
        if recursive:
            cmd.append("-r")
        # Ensure path exists before passing to grep
        full_search_path = os.path.join(wrapper.context.working_directory, path)
        if not os.path.exists(full_search_path):
             return f"Error: Search path does not exist: {full_search_path}"
             
        cmd.extend([pattern, full_search_path])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=wrapper.context.working_directory,
            encoding='utf-8', errors='ignore' # Keep encoding handling
        )
        
        logger.info(f"Executed grep search for pattern: {pattern} in path: {path}")
        
        if result.returncode == 0:
            return f"Found matches:\n{result.stdout}"
        elif result.returncode == 1:
            return "No matches found"
        else:
            logger.error(f"Grep error: {result.stderr}")
            # Check if error is due to grep not found
            if "not recognized" in result.stderr or "not found" in result.stderr:
                 return "Error: 'grep' command not found or not recognized."
            return f"Error running grep: {result.stderr}"
    except FileNotFoundError:
         logger.error("'grep' command not found. Is it installed and in PATH?")
         return "Error: 'grep' command not found."
    except Exception as e:
        logger.error(f"Error with grep operation: {str(e)}")
        return f"Error with grep: {str(e)}"

# Define Pydantic models for batch_execute tasks
class TaskDefinition(BaseModel):
    model_config = ConfigDict(extra='forbid')

    tool: str
    params: Optional[Dict[str, Any]] = None

# Explicitly define the batch_execute tool without using the decorator
async def _batch_execute_impl(
    wrapper: RunContextWrapper[AgentContext],
    tasks: List[Any] # Change type hint to List[Any] to reflect reality
) -> str:
    """Internal implementation for executing multiple tasks in parallel."""
    if "batch" not in wrapper.context.allowed_tools:
        logger.warning("Batch tool not allowed in this context")
        return "Batch tool not allowed in this context"

    results = []

    async def execute_task(task_input: Any): # Rename param to task_input
        # Validate task_input and parse into TaskDefinition
        if isinstance(task_input, dict):
            try:
                task_def = TaskDefinition.model_validate(task_input)
            except Exception as pydantic_error:
                logger.warning(f"Failed to parse task dictionary into TaskDefinition: {task_input}. Error: {pydantic_error}")
                return f"Invalid task format: {task_input}"
        else:
            # Handle cases where the LLM didn't provide a dictionary
            logger.warning(f"Received invalid task format (expected dict): {task_input}")
            return f"Invalid task format: {task_input}"

        # Proceed with validated task_def
        tool_name = task_def.tool
        params_dict = task_def.params if task_def.params is not None else {}

        # Find the tool function (using self.tool_map from the agent context later)
        # For now, assume a static map - needs refactoring if agent instance is not available here
        tool_map = {
            "edit": edit_file,
            "read": read_file,
            "bash": run_bash,
            "ls": list_files,
            "git": git_operations,
            "grep": grep_files
        }

        tool_func = tool_map.get(tool_name)
        if not tool_func:
            logger.warning(f"Tool not found: {tool_name}")
            return f"Tool {tool_name} not found"

        # Execute the tool
        try:
            return await tool_func(wrapper, **params_dict)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return f"Error executing {tool_name}: {str(e)}"

    # Execute all tasks in parallel
    tasks_to_run = [execute_task(task) for task in tasks] # Pass raw task input
    results = await asyncio.gather(*tasks_to_run)

    # Format results
    output = "Batch execution results:\n"
    # When formatting, try to get the original tool name if parsing failed
    for i, (task_input, result) in enumerate(zip(tasks, results)):
        tool_name_display = task_input.get('tool', 'unknown') if isinstance(task_input, dict) else 'invalid_format'
        output += f"\nTask {i+1} ({tool_name_display}):\n{result}\n"

    logger.info(f"Completed batch execution of {len(tasks)} tasks")
    return output

# Define the schema manually for the List[TaskDefinition] input
# This schema allows the list of tasks with tool (string) and params (object)
batch_execute_schema = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": TaskDefinition.model_json_schema() # Use Pydantic's schema for the items
        }
    },
    "required": ["tasks"]
}

# Create the FunctionTool instance manually
# Note: We are NOT using ensure_strict_json_schema here
batch_execute = FunctionTool(
    name="batch_execute",
    description="Execute multiple tasks in parallel. Each task should be a dict with: tool (str), params (dict)",
    params_json_schema=batch_execute_schema,
    on_invoke_tool=_batch_execute_impl, # Point to the internal implementation
)

@function_tool
async def spawn_task(
    wrapper: RunContextWrapper[AgentContext],
    task_name: str,
    prompt: str,
    allowed_tools: List[str] = None
) -> str:
    """Spawn a sub-agent to handle a specific task."""
    if "task" not in wrapper.context.allowed_tools:
        logger.warning("Task spawning not allowed in this context")
        return "Task spawning not allowed in this context"

    # Default tools if none provided
    if allowed_tools is None:
        allowed_tools = ["edit", "read", "bash"]

    # --- Fix: Ensure tool names passed to sub-agent are clean ---
    # Remove potential 'functions.' prefix if present (e.g., from LLM output)
    # Make sure the input is actually a list of strings before processing
    clean_allowed_tools = []
    if isinstance(allowed_tools, list):
        clean_allowed_tools = [name.split('.')[-1] if isinstance(name, str) else name for name in allowed_tools]
    else:
        logger.warning(f"spawn_task received non-list allowed_tools: {allowed_tools}. Using defaults.")
        clean_allowed_tools = ["edit", "read", "bash"] # Fallback to defaults
    # -------------------------------------------------------------

    try:
        # Check if we already have this sub-agent
        if task_name not in wrapper.context.sub_agents:
            from importlib import import_module

            module = import_module(__name__)
            ProgrammableAgent = getattr(module, "ProgrammableAgent")

            # Use the cleaned tool names
            sub_agent = ProgrammableAgent(allowed_tools=clean_allowed_tools)
            wrapper.context.sub_agents[task_name] = sub_agent
        else:
            sub_agent = wrapper.context.sub_agents[task_name]

        # Execute the task with the sub-agent
        # Note: The sub-agent execute method doesn't need the wrapper, just the prompt and working_dir
        result = await sub_agent.execute(prompt, wrapper.context.working_directory)
        logger.info(f"Completed task: {task_name}")
        return f"Task '{task_name}' completed:\\n{result}"
    except Exception as e:
        logger.error(f"Error in task {task_name}: {str(e)}")
        return f"Error in task '{task_name}': {str(e)}"
    
function_tool
async def code_executor(
        wrapper: RunContextWrapper[AgentContext],
        prompt: str,
        allowed_tools: List[str] = None 
) -> str:
    """Execute code as a tool within your agent system"""

    if allowed_tools is None:
        allowed_tools = ["edit", "read", "bash"]

    cmd = f'clause -P "{prompt}" --allow_tools {" ".join(allowed_tools)}'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=wrapper.context.working_directory)
        return result.stdout 
    except Exception as e:
        return f"Error: {e}"
    
# Create an agent that can use Code
planning_agent = Agent(
    name="Planning Agent",
    instructions="You create detailed plans and specifications",
    tools=[code_executor]
)

@function_tool
async def glob_search(
    wrapper: RunContextWrapper[AgentContext],
    pattern: str,
    # recursive: bool = True # rglob handles recursion implicitly
) -> str:
    """Find files matching a glob pattern using pathlib for robust recursion."""
    try:
        base_path = Path(wrapper.context.working_directory)
        # Use rglob for recursive search if pattern contains **
        if "**" in pattern:
            # rglob expects pattern relative to the base path
            # Correctly handle path separation for pattern matching
            files = list(base_path.rglob(pattern))
        else:
            # glob is non-recursive
            files = list(base_path.glob(pattern))
        
        # Convert Path objects to strings for output
        file_paths = [str(f.relative_to(base_path)) for f in files] # Show relative paths
        
        logger.info(f"Executed glob search with pattern: '{pattern}' in '{base_path}'")
        
        if file_paths:
            return "Found files:\n" + "\n".join(file_paths)
        else:
            return f"No files found matching pattern: {pattern}"
    except Exception as e:
        logger.error(f"Error with glob search: {str(e)}")
        return f"Error with glob search: {str(e)}"

# Advanced batch tool - Manual Definition
async def _advanced_batch_impl(
    wrapper: RunContextWrapper[AgentContext],
    operations: List[Dict[str, Any]],
    parallel: bool = True,
    continue_on_error: bool = True
) -> str:
    """Internal implementation for advanced batch execution."""
    if "batch" not in wrapper.context.allowed_tools: # Assuming advanced_batch uses the same 'batch' permission
        logger.warning("Advanced Batch tool not allowed in this context")
        return "Advanced Batch tool not allowed in this context"
    
    results = []
    errors = []
    
    # Define execute_operation locally or ensure it's accessible
    async def execute_operation(wrapper, operation, index):
        """Helper function to execute a single operation."""
        op_type = operation.get("type")
        
        if op_type == "tool":
            tool_name = operation.get("tool")
            params = operation.get("params", {})
            
            # Get the tool function (needs access to tool_map or context)
            tool_map = {
                "edit": edit_file,
                "read": read_file,
                "bash": run_bash,
                "ls": list_files,
                "git": git_operations,
                "grep": grep_files,
                "glob": glob_search
                # Note: Doesn't include batch/task/advanced_batch to avoid recursion issues here
            }
            
            tool_func = tool_map.get(tool_name)
            if tool_func:
                # Check if tool_func is itself a FunctionTool instance or a direct async callable
                if isinstance(tool_func, FunctionTool):
                     # If it's a FunctionTool, invoke its handler
                    return await tool_func.on_invoke_tool(wrapper, json.dumps(params))
                else:
                    # Assume it's a direct async callable decorated with @function_tool
                    return await tool_func(wrapper, **params)
            else:
                logger.warning(f"Unknown tool in advanced_batch: {tool_name}")
                return f"Unknown tool: {tool_name}"
        
        elif op_type == "task":
            task_name = operation.get("name", f"task_{index}")
            prompt = operation.get("prompt")
            allowed_tools = operation.get("allowed_tools", ["edit", "read", "bash"])
            
            # Need to call the spawn_task tool correctly
            # Assuming spawn_task is available via wrapper or context
            # This might require passing the ProgrammableAgent instance or tool_map into context
            # For now, we call the global spawn_task which is a FunctionTool instance
            spawn_params = {"task_name": task_name, "prompt": prompt, "allowed_tools": allowed_tools}
            return await spawn_task.on_invoke_tool(wrapper, json.dumps(spawn_params))
        
        else:
            logger.warning(f"Unknown operation type: {op_type}")
            return f"Unknown operation type: {op_type}"

    if parallel:
        futures = []
        # Use the executor from the context
        with wrapper.context.executor as executor:
            for i, op in enumerate(operations):
                # Need to ensure execute_operation is awaitable if called via executor.submit
                # This might be complex; switching to asyncio.gather for async parallel execution
                # future = executor.submit(execute_operation, wrapper, op, i)
                # futures.append(future)
                pass # Refactoring needed for parallel execution with async/await
            
            # Using asyncio.gather for parallel async execution instead of ThreadPoolExecutor
            tasks_to_run = [execute_operation(wrapper, op, i) for i, op in enumerate(operations)]
            results_or_errors = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            for i, res_or_err in enumerate(results_or_errors):
                if isinstance(res_or_err, Exception):
                    error_msg = f"Operation {i} failed: {str(res_or_err)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if not continue_on_error:
                        break # Or handle differently
                else:
                    results.append((i, res_or_err))

    else: # Sequential execution
        for i, op in enumerate(operations):
            try:
                result = await execute_operation(wrapper, op, i)
                results.append((i, result))
            except Exception as e:
                error_msg = f"Operation {i} failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                if not continue_on_error:
                    break
    
    # Format output (remains the same)
    output = "Advanced Batch execution completed:\n\n"
    output += f"Successful operations: {len(results)}\n"
    output += f"Failed operations: {len(errors)}\n\n"
    
    if results:
        output += "Results:\n"
        for i, result in results:
             # Ensure result is a string before slicing
            result_str = str(result) if result is not None else "None"
            output += f"Operation {i}: {result_str[:100]}{'...' if len(result_str) > 100 else ''}\n"
    
    if errors:
        output += "\nErrors:\n"
        for error in errors:
            output += f"{error}\n"
    
    logger.info(f"Completed advanced batch execution: {len(results)} successful, {len(errors)} failed")
    return output

# Manually define schema for advanced_batch
advanced_batch_schema = {
    "type": "object",
    "properties": {
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                # Allow any properties within each operation dict
                # "additionalProperties": True # This is usually discouraged but needed here
            },
            "description": "List of operations to execute."
        },
        "parallel": {
            "type": "boolean",
            "default": True,
            "description": "Execute operations in parallel."
        },
        "continue_on_error": {
            "type": "boolean",
            "default": True,
            "description": "Continue execution even if an operation fails."
        }
    },
    "required": ["operations"]
}

# Create FunctionTool instance for advanced_batch
advanced_batch = FunctionTool(
    name="advanced_batch",
    description="Execute a batch of operations with advanced control (sequential/parallel, error handling).",
    params_json_schema=advanced_batch_schema,
    on_invoke_tool=_advanced_batch_impl
)

# @function_tool # Removed decorator
# async def advanced_batch(
#     wrapper: RunContextWrapper[AgentContext],
#     operations: List[Dict[str, Any]],
#     parallel: bool = True,
#     continue_on_error: bool = True
# ) -> str:
#     """Execute a batch of operations with advanced control.
#     ...
#     """
#     # Implementation moved to _advanced_batch_impl

class ProgrammableAgent:
    """A flexible agent system for automating development workflows.
    
    This agent provides various tools for code manipulation, file operations,
    git operations, and task management. It can be configured with specific
    allowed tools and uses Azure OpenAI for intelligence.
    
    Attributes:
        allowed_tools (List[str]): List of tool names that this agent is allowed to use
        tool_map (Dict[str, Callable]): Mapping of tool names to their implementations
        agent (Agent): The underlying agent implementation
    """
    
    def __init__(self, allowed_tools: List[str] = None):
        """Initialize the programmable agent.
        
        Args:
            allowed_tools (List[str], optional): List of tool names to enable.
                Defaults to all available tools if None.
        """
        # Clean the incoming allowed_tools list immediately
        raw_allowed_tools = allowed_tools or ["edit", "read", "mkdir", "bash", "ls", "git", "grep", "glob", "batch", "task", "advanced_batch"]
        cleaned_allowed_tools = []
        if isinstance(raw_allowed_tools, list):
            cleaned_allowed_tools = [name.split('.')[-1] if isinstance(name, str) else name for name in raw_allowed_tools]
        else:
             # Fallback if input is somehow not a list (though default makes this unlikely)
            logger.warning(f"ProgrammableAgent received non-list allowed_tools: {raw_allowed_tools}. Using defaults.")
            cleaned_allowed_tools = ["edit", "read", "mkdir", "bash", "ls", "git", "grep", "glob", "batch", "task", "advanced_batch"]

        self.allowed_tools = cleaned_allowed_tools # Store the cleaned list

        # Map tool names to actual functions/FunctionTool instances
        self.tool_map = {
            "edit": edit_file,
            "read": read_file,
            "mkdir": mkdir,
            "bash": run_bash,
            "ls": list_files,
            "git": git_operations,
            "grep": grep_files,
            "glob": glob_search,
            "batch": batch_execute,
            "task": spawn_task,
            "advanced_batch": advanced_batch
        }
        
        # Select tools based on the *cleaned* allowed list
        selected_tools = []
        for tool_name in self.allowed_tools: # Use the cleaned list
            tool_impl = self.tool_map.get(tool_name)
            if tool_impl:
                selected_tools.append(tool_impl)
            else:
                 # This warning should now only trigger if a *cleaned* name is invalid
                logger.warning(f"Tool '{tool_name}' listed in allowed_tools but not found in tool_map.")
        
        deployment_name = gemini_config.programmable_deployment
        
        self.agent = Agent[AgentContext](
            name="Programmable Agent",
            instructions="""
            You are a programmable agent with advanced capabilities:
            
            1. File operations: edit, read, ls, glob
            2. Search operations: grep for text search, glob for file pattern matching
            3. Shell operations: bash for running commands
            4. Git operations: git for version control
            5. Parallel execution: batch for running multiple operations in parallel
            6. Task spawning: task for creating sub-agents to handle complex workflows
            
            When using batch operations, structure them as:
            - For simple parallel tasks: use batch with a list of tool calls
            - For complex workflows: use task to spawn specialized sub-agents
            
            Always explain what you're doing before executing commands.
            Use grep to search for patterns in files.
            Use glob to find files matching patterns.
            Use batch when you need to perform multiple operations efficiently.
            Use task to delegate complex sub-tasks to specialized agents.
            """,
            tools=selected_tools, # Pass the correctly selected tools
            model=deployment_name
        )

    def create_context(self, working_dir: str = ".") -> AgentContext:
        """Create an AgentContext for this agent.

        Args:
            working_dir (str): The working directory for the context.

        Returns:
            AgentContext: An initialized context object.
        """
        return AgentContext(
            working_directory=os.path.abspath(working_dir),
            allowed_tools=self.allowed_tools
            # executor and sub_agents will be initialized by AgentContext.__post_init__
        )

    async def execute(self, prompt: str, working_dir: str = "."):
        """Execute a prompt with the agent."""
        context = self.create_context(working_dir) # Use the new method

        result = await Runner.run(
            starting_agent=self.agent,
            input=prompt,
            context=context 
        )

        return result.final_output 
    
# Command-line interface
async def main():
    parser = argparse.ArgumentParser(
        description=f"{Fore.CYAN}Programmable Agent CLI{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}Automate code, file, and git operations with AI.{Style.RESET_ALL}",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""{Fore.GREEN}Examples:{Style.RESET_ALL}
  python coding_agent.py "Edit README.md with new content" --allow-tools edit read --working-dir .
  python coding_agent.py "List all Python files" --allow-tools ls --working-dir ./src
"""
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help=f"{Fore.MAGENTA}The prompt to execute (in quotes).{Style.RESET_ALL}"
    )
    parser.add_argument(
        "--allow-tools", "-t",
        nargs="+",
        default=["edit", "read", "mkdir", "bash", "ls", "git", "grep", "glob", "batch", "task", "advanced_batch"],
        choices=["edit", "read", "mkdir", "bash", "ls", "git", "grep", "glob", "batch", "task", "advanced_batch"],
        metavar="TOOL",
        help=f"{Fore.MAGENTA}Tools to allow (space-separated). Default: all tools.{Style.RESET_ALL}"
    )
    parser.add_argument(
        "--working-dir", "-d",
        default=".",
        help=f"{Fore.MAGENTA}Working directory. Default: current directory.{Style.RESET_ALL}"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Programmable Agent 1.0"
    )

    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        print(f"\n{Fore.RED}Error: You must provide a prompt to execute.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.CYAN}Running Programmable Agent...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Prompt:{Style.RESET_ALL} {args.prompt}")
    print(f"{Fore.YELLOW}Allowed tools:{Style.RESET_ALL} {', '.join(args.allow_tools)}")
    print(f"{Fore.YELLOW}Working directory:{Style.RESET_ALL} {args.working_dir}\n")

    agent = ProgrammableAgent(allowed_tools=args.allow_tools)
    result = await agent.execute(args.prompt, args.working_dir)
    print(f"{Fore.GREEN}Result:{Style.RESET_ALL}\n{result}")

if __name__ == "__main__":
    asyncio.run(main())