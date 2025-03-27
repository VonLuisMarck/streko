![Project Banner](docs/header_image.png)

# *GenAI-Enhanced C2 Framework*
A research framework demonstrating the impact of Generative AI integration with command and control systems for security testing and research.

## *Overview*

This project demonstrates how Large Language Models (LLMs) can enhance security research by combining traditional C2 capabilities with AI-driven features. This framework is explicitly designed for controlled security testing environments to study and better understand evasion techniques and defensive strategies.

## *Key Capabilities*

1. Natural language control of agents through an AI-powered chat interface
2. Dynamic code generation from conversational instructions
3. Intelligent code obfuscation to study evasion techniques
4. Attack path analysis based on system reconnaissance data
5. Cross-platform agent support with varying functionality levels

## *Architecture*

1. The framework consists of three main components:
2. C2 Server: Flask-based web application providing both API endpoints for agents and a web interface for operators
3. Agent Scripts: Python clients that connect to the C2 server, from basic to advanced implementations
4. LLM Integration: OpenAI API integration for code generation, obfuscation, and attack path analysis

# *Setup Instructions*

## Prerequisites

1. Python 3.8+
2. Flask and other dependencies
3. OpenAI API key (for AI features)
4. Isolated testing environment

## Installation
Clone the repository

```bash
git clone https://github.com/yourusername/genai-c2-framework.git
cd genai-c2-framework
```
### Create and activate a virtual environment

#### On Linux/macOS


```bash
python -m venv venv
source venv/bin/activate
```
#### On Windows
``` ps
python -m venv venv
venv\Scripts\activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```


#### Set up environment variables

```bash
# Linux/macOS
export OPENAI_API_KEY="your-api-key-here"
```
```ps
# Windows
set OPENAI_API_KEY=your-api-key-here
```

#### Create the required directory structure

```bash
mkdir -p templates
#Place the HTML template
#Save the provided template code as templates/index.html
```
#### Starting the C2 Server
Run the Flask application:

```bash
python app.py
```
Access the web interface at: 
127.0.0.1:5000

### Agent Deployment
Three agent implementations are provided, with increasing levels of sophistication:

#### Basic Test Agent
```bash
python basic_test_agent.py --server http://your-server-ip:5000
```
Ideal for initial connection testing and simple task execution.

#### Interactive Test Agent
```bash
python interactive_agent.py --server http://your-server-ip:5000
```
Provides a command-line interface for interaction with the agent and viewing task history.

#### Advanced Test Agent
```bash
python advanced_agent.py --server http://your-server-ip:5000 [options]
```
Additional options:
```bash
    --interval, -i: Check interval in seconds (default: 30)
    --jitter, -j: Random jitter in seconds (default: 5)
    --id: Specify custom agent ID
    --evade, -e: Enable evasion techniques
    --quiet, -q: Non-interactive mode
    --debug, -d: Enable debug logging
```
Key Features
1. Web Dashboard
The C2 server provides a comprehensive web interface with:

```bash
. Connected agent management
. Task creation and monitoring
. Results visualization
. AI-powered features
```
2. AI-Powered Chat Interface

Interact with agents using natural language, for example:

`Agent> Show me all running processes`

The system will:

```bash
    . Process your request using the LLM
    . Generate appropriate Python code
    . Execute the code on the target agent
    . Return the results in a conversational format
```
3. Code Obfuscation
```bash
    . Study evasion techniques by obfuscating code with AI:
    . Input original code
    . Select target security product
    . Generate obfuscated variants
    . Deploy testing agents
```
4. Attack Path Analysis

Analyze reconnaissance data to identify potential weaknesses:

    . Collect system information from agents
    . Process using AI to identify vulnerabilities
    . Receive recommendations based on MITRE ATT&CK framework
    . Get implementation suggestions for security testing

**Use only in authorized environments where you have explicit permission
Never deploy agents on production systems or systems you don't own
Contain all testing within isolated lab networks
Document all research activities conducted with this framework**

# Troubleshooting
## API Key Issues
Ensure your OpenAI API key is set correctly
The framework will use mock implementations if no API key is available

## Connection Problems

Verify network connectivity between agents and C2 server
Check for firewall rules blocking traffic
## Agent Execution Errors
Ensure Python environment has necessary permissions
Check agent logs for detailed error messages

## Advanced Configuration
Custom Tasks
Create task templates by modifying the mock_generate_code function in app.py.

## Extended Agent Capabilities
The agent architecture supports adding custom modules by extending the agent classes.

# Acknowledgements
This project was created for research into GenAI-enhanced security tools at CrowdStrike.

