// Global variables
let currentConversationId = null;
let selectedAgentId = null;
let startTime = new Date();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Add tab switching functionality
    setupTabs();
    
    // Start timers
    updateTime();
    setInterval(updateTime, 1000);
    
    // Setup event listeners
    setupEventListeners();
    
    // Load settings
    loadSettings();
    
    // Initialize terminal
    setupTerminal();
    
    // Add Soviet hacker theme
    applySovietTheme();
});

// Tab functionality
function setupTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-tab');
            showTab(tabId, this);
        });
    });
}

function showTab(tabId, clickedElement) {
    // Update navigation items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    
    if (clickedElement) {
        clickedElement.classList.add('active');
    } else {
        // Find and activate the corresponding nav item
        document.querySelector(`.nav-item[data-tab="${tabId}"]`).classList.add('active');
    }
    
    // Update tab content
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabId}-tab`).classList.add('active');
    
    // Update header title
    const title = clickedElement ? clickedElement.querySelector('span').textContent : 
        document.querySelector(`.nav-item[data-tab="${tabId}"] span`).textContent;
    document.getElementById('current-tab-title').textContent = title;
    
    // Set subtitle based on tab with Soviet theme
    const subtitles = {
        'command-hub': '// Operation Control Center',
        'targets': '// Compromised Systems',
        'terminal': '// Command Execution Interface',
        'obfuscator': '// Payload Evasion Module',
        'attack-vectors': '// Security Analysis System',
        'config': '// System Configuration'
    };
    document.getElementById('current-tab-subtitle').textContent = subtitles[tabId] || '';
}

function setupEventListeners() {
    // Launch exploit modal
    document.getElementById('refresh-btn').addEventListener('click', showRefreshConfirmation);
    
    // Task type change
    document.getElementById('task_type').addEventListener('change', function() {
        const customBlock = document.getElementById('customCodeBlock');
        if (this.value === 'custom') {
            customBlock.style.display = 'block';
        } else {
            customBlock.style.display = 'none';
        }
    });
    
    // Script file upload
    document.getElementById('script_file').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('custom_code').value = e.target.result;
        };
        reader.readAsText(file);
    });
    
    // Obfuscator
    document.getElementById('obfuscate-btn').addEventListener('click', obfuscateCode);
    document.getElementById('deploy-obfuscated').addEventListener('click', showDeployModal);
    document.getElementById('copy-obfuscated').addEventListener('click', copyObfuscatedCode);
    
    // Attack paths analysis
    document.getElementById('analysis-agent-select').addEventListener('change', function() {
        document.getElementById('analyze-btn').disabled = !this.value;
    });
    document.getElementById('analyze-btn').addEventListener('click', function() {
        analyzeAttackPaths(document.getElementById('analysis-agent-select').value);
    });
    
    // Settings
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
}

// Update time displays
function updateTime() {
    // Update uptime
    const uptime = Math.floor((new Date() - startTime) / 1000);
    const hours = Math.floor(uptime / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((uptime % 3600) / 60).toString().padStart(2, '0');
    const seconds = Math.floor(uptime % 60).toString().padStart(2, '0');
    document.getElementById('uptime').textContent = `${hours}:${minutes}:${seconds}`;
    
    // Update success rate with slight variations to look dynamic
    if (Math.random() > 0.8) {
        const successRate = 93 + Math.floor(Math.random() * 7);
        document.getElementById('success-rate').textContent = `${successRate}%`;
    }
    
    // Update Moscow time
    updateMoscowTime();
}

// Update Moscow time display
function updateMoscowTime() {
    const moscowTimeElement = document.getElementById('moscow-time');
    if (moscowTimeElement) {
        // Moscow is UTC+3
        const now = new Date();
        const moscowDate = new Date(now.getTime() + (3 * 60 * 60 * 1000));
        const hours = moscowDate.getUTCHours().toString().padStart(2, '0');
        const mins = moscowDate.getUTCMinutes().toString().padStart(2, '0');
        moscowTimeElement.textContent = `${hours}:${mins}`;
    }
}

// Modal functions
function showTaskModal(agentId) {
    document.getElementById('agent_id').value = agentId;
    document.getElementById('taskModal').classList.add('show');
}

function hideTaskModal() {
    document.getElementById('taskModal').classList.remove('show');
}

function showRefreshConfirmation() {
    document.getElementById('refreshModal').classList.add('show');
}

function hideRefreshConfirmation() {
    document.getElementById('refreshModal').classList.remove('show');
}

function showDeployModal() {
    document.getElementById('deployModal').classList.add('show');
}

function hideDeployModal() {
    document.getElementById('deployModal').classList.remove('show');
}

function showPayloadModal() {
    document.getElementById('payloadModal').classList.add('show');
}

function hidePayloadModal() {
    document.getElementById('payloadModal').classList.remove('show');
}

function showIntelModal() {
    document.getElementById('intelModal').classList.add('show');
}

function hideIntelModal() {
    document.getElementById('intelModal').classList.remove('show');
}

// Payload/Intel viewers
function viewPayload(taskId, code) {
    document.getElementById('payload-content').textContent = code;
    showPayloadModal();
}

function viewIntel(data) {
    document.getElementById('intel-content').textContent = JSON.stringify(data, null, 2);
    showIntelModal();
}

// Task submission
function submitTask() {
    const agentId = document.getElementById('agent_id').value;
    const taskType = document.getElementById('task_type').value;
    const customCode = document.getElementById('custom_code').value;
    
    const taskData = {
        agent_id: agentId,
        task_type: taskType
    };
    
    if (taskType === 'custom' && customCode.trim() !== '') {
        taskData.custom_code = customCode;
    }
    
    // Send task to server
    fetch('/create_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        hideTaskModal();
        showHackerAlert(`★ Exploit launched with ID: ${data.task_id.substring(0, 8)}... ★`);
        setTimeout(() => location.reload(), 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        showHackerAlert('Launch failed. Check your payload and try again.');
    });
}

// Hacker-style alert
function showHackerAlert(message) {
    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = 'hacker-alert';
    alertEl.style.position = 'fixed';
    alertEl.style.top = '20px';
    alertEl.style.left = '50%';
    alertEl.style.transform = 'translateX(-50%)';
    alertEl.style.padding = '15px 25px';
    alertEl.style.background = 'rgba(10, 10, 10, 0.95)';
    alertEl.style.color = '#cc0000';
    alertEl.style.border = '1px solid #cc0000';
    alertEl.style.borderRadius = '0';
    alertEl.style.fontFamily = '"Courier New", monospace';
    alertEl.style.fontSize = '14px';
    alertEl.style.zIndex = '2000';
    alertEl.style.boxShadow = '0 0 20px rgba(204, 0, 0, 0.4)';
    alertEl.style.textTransform = 'uppercase';
    alertEl.style.letterSpacing = '1px';
    alertEl.innerText = message;
    
    // Add to body
    document.body.appendChild(alertEl);
    
    // Remove after 3 seconds
    setTimeout(() => {
        alertEl.style.opacity = '0';
        alertEl.style.transition = 'opacity 0.5s';
        setTimeout(() => document.body.removeChild(alertEl), 500);
    }, 3000);
}

// Refresh dashboard
function refreshDashboard() {
    location.reload();
    hideRefreshConfirmation();
}

// Settings
function loadSettings() {
    const apiKey = localStorage.getItem('openai_api_key') || '';
    const model = localStorage.getItem('default_model') || 'gpt-4o';
    const opName = localStorage.getItem('operation_name') || 'FANCY SPIDER';
    
    document.getElementById('api-key').value = apiKey;
    document.getElementById('default-model').value = model;
    document.getElementById('operation-name').value = opName;
    
    // Update header with operation name
    const logoHeader = document.querySelector('.logo h1');
    if (logoHeader && opName) {
        logoHeader.innerHTML = `★ ${opName} ★`;
    }
}

function saveSettings() {
    const apiKey = document.getElementById('api-key').value;
    const model = document.getElementById('default-model').value;
    const opName = document.getElementById('operation-name').value;
    
    localStorage.setItem('openai_api_key', apiKey);
    localStorage.setItem('default_model', model);
    localStorage.setItem('operation_name', opName);
    
    // Update header with new operation name
    const logoHeader = document.querySelector('.logo h1');
    if (logoHeader && opName) {
        logoHeader.innerHTML = `★ ${opName} ★`;
    }
    
    showHackerAlert('Configuration saved successfully');
}

// Code obfuscation functions
function obfuscateCode() {
    const code = document.getElementById('original-code').value.trim();
    if (!code) {
        showHackerAlert('Enter code to obfuscate');
        return;
    }
    
    const language = document.getElementById('code-language').value;
    const targetSecurity = document.getElementById('target-security').value;
    
    // Show loading
    document.getElementById('obfuscate-btn').disabled = true;
    document.getElementById('obfuscate-btn').innerHTML = '<div class="spinner" style="width: 16px; height: 16px;"></div> OBFUSCATING...';
    
    // Call obfuscation API
    fetch('/obfuscate_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            code: code,
            language: language,
            target_security: targetSecurity
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button
        document.getElementById('obfuscate-btn').disabled = false;
        document.getElementById('obfuscate-btn').innerHTML = '<i class="fas fa-magic"></i> OBFUSCATE';
        
        if (data.status === 'success') {
            // Show results
            document.getElementById('obfuscated-code').textContent = data.obfuscated_code;
            document.getElementById('obfuscation-explanation').innerHTML = data.explanation;
            document.getElementById('obfuscation-result').style.display = 'block';
            showHackerAlert('★ Obfuscation complete ★');
        } else {
            showHackerAlert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showHackerAlert('Obfuscation failed. Try again.');
        
        // Reset button
        document.getElementById('obfuscate-btn').disabled = false;
        document.getElementById('obfuscate-btn').innerHTML = '<i class="fas fa-magic"></i> OBFUSCATE';
    });
}

function copyObfuscatedCode() {
    const code = document.getElementById('obfuscated-code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        showHackerAlert('Payload copied to clipboard');
    });
}

function deployCode() {
    const agentId = document.getElementById('deploy-agent-select').value;
    if (!agentId) {
        showHackerAlert('Select a target to deploy payload');
        return;
    }
    
    const code = document.getElementById('obfuscated-code').textContent;
    
    // Create task with obfuscated code
    fetch('/create_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agent_id: agentId,
            task_type: 'custom',
            custom_code: code
        })
    })
    .then(response => response.json())
    .then(data => {
        hideDeployModal();
        showHackerAlert(`★ Payload deployed to target (ID: ${data.task_id.substring(0, 8)}...) ★`);
        setTimeout(() => location.reload(), 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        showHackerAlert('Payload deployment failed. Check target status.');
    });
}

// Attack vector analysis
function analyzeAttackPaths(agentId) {
    if (!agentId) return;
    
    // Get analysis type
    const analysisType = document.querySelector('input[name="analysisType"]:checked').value;
    
    // Show loading
    document.getElementById('analysis-loading').style.display = 'block';
    document.getElementById('analysis-result').style.display = 'none';
    
    // Show attack paths tab if called from another tab
    showTab('attack-vectors');
    
    // Set selected agent
    document.getElementById('analysis-agent-select').value = agentId;
    
    // Prepare payload
    let payload = {
        agent_id: agentId,
        analysis_type: analysisType
    };
    
    // For advanced analysis, include command to download and execute winpeas
    if (analysisType === 'advanced') {
        payload.command = "download and execute winpeas from /scripts";
    }
    
    // Call analysis API
    fetch('/analyze_attack_paths', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading
        document.getElementById('analysis-loading').style.display = 'none';
        
        // Show results
        document.getElementById('analysis-content').innerHTML = formatAnalysis(data.analysis);
        document.getElementById('analysis-result').style.display = 'block';
        showHackerAlert('★ Attack vector analysis complete ★');
    })
    .catch(error => {
        console.error('Error:', error);
        showHackerAlert('Analysis failed. Check target connection.');
        document.getElementById('analysis-loading').style.display = 'none';
    });
}

function formatAnalysis(analysis) {
    // Convert markdown-like format to HTML with Soviet styling
    let formatted = analysis
        .replace(/\n\n/g, '<br><br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#cc0000;">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em style="color:#d4af37;">$1</em>')
        .replace(/^#{1,6}\s+(.*?)$/gm, (match, title) => {
            const level = match.split(' ')[0].length;
            return `<h${level} style="color:#cc0000;margin-top:1rem;margin-bottom:0.5rem;font-family:Courier New,monospace;">★ ${title}</h${level}>`;
        })
        .replace(/```(.*?)```/gs, (match, code) => {
            return `<pre style="background:rgba(0,0,0,0.5);padding:10px;border-radius:0;border-left:3px solid #cc0000;overflow-x:auto;font-family:'Courier New',monospace;">${code}</pre>`;
        });
    
    // Highlight security terms
    const securityTerms = [
        'Vulnerability', 'Critical', 'High', 'Medium', 'Low',
        'Attack Vector', 'Exploitation', 'Privilege Escalation',
        'Persistence', 'Defense Evasion', 'Credential Access',
        'Discovery', 'Lateral Movement', 'Collection', 'Exfiltration',
        'Command and Control', 'Impact', 'Execution'
    ];
    
    securityTerms.forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'g');
        formatted = formatted.replace(regex, `<span style="color:#d4af37;">${term}</span>`);
    });
    
    return formatted;
}

// Terminal functionality
function setupTerminal() {
    const terminalOutput = document.getElementById('terminal-output');
    const commandInput = document.getElementById('command-input');
    const executeButton = document.getElementById('execute-command');
    const targetSelector = document.getElementById('terminal-target');
    const languageSelector = document.getElementById('language-selector');
    
    if (executeButton) {
        executeButton.addEventListener('click', function() {
            executeCommand();
        });
        
        if (commandInput) {
            commandInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.ctrlKey) {
                    executeButton.click();
                    e.preventDefault();
                }
            });
        }
    }
    
    function executeCommand() {
        const command = commandInput.value.trim();
        const target = targetSelector.value;
        const language = languageSelector.value;
        
        if (!command) {
            addTerminalEntry('error', 'Please enter a command');
            return;
        }
        
        if (!target) {
            addTerminalEntry('error', 'Please select a target');
            return;
        }
        
        // Add command to terminal
        addTerminalEntry('command', command, `COMMAND (${language.toUpperCase()})`);
        
        // Send to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: target,
                message: command,
                execution_type: language
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'message_processed') {
                // Get the task to show the generated code
                fetch(`/get_task/${data.task_id}`)
                    .then(response => response.json())
                    .then(taskData => {
                        // Show the generated code
                        addTerminalEntry('code', taskData.code, 'GENERATED CODE');
                        
                        // Show execution result if available
                        if (data.execution_completed) {
                            addTerminalEntry('result', data.ai_response, 'EXECUTION RESULT');
                        } else {
                            addTerminalEntry('result', 'Task queued but execution result not yet available. The agent may be offline or busy.', 'STATUS');
                        }
                    })
                    .catch(error => {
                        addTerminalEntry('error', `Failed to get task details: ${error}`);
                    });
            } else {
                addTerminalEntry('error', data.message || 'Unknown error occurred');
            }
        })
        .catch(error => {
            addTerminalEntry('error', `Request failed: ${error}`);
        });
        
        // Clear the input
        commandInput.value = '';
    }
    
    function addTerminalEntry(type, content, label) {
        const entry = document.createElement('div');
        entry.className = `terminal-entry terminal-${type}`;
        
        const header = document.createElement('div');
        header.className = 'entry-header';
        header.innerHTML = (label || type.toUpperCase()) + ' <span style="color:#d4af37;">[' + new Date().toTimeString().split(' ')[0] + ']</span>';
        entry.appendChild(header);
        
        const contentElement = document.createElement('div');
        contentElement.className = 'entry-content';
        
        if (typeof content === 'object') {
            // Format object as JSON
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(content, null, 2);
            contentElement.appendChild(pre);
        } else if (type === 'code') {
            // Format code with pre tags
            const pre = document.createElement('pre');
            pre.textContent = content;
            contentElement.appendChild(pre);
        } else {
            contentElement.innerHTML = content
                .replace(/error/gi, '<span style="color:#cc0000;">error</span>')
                .replace(/warning/gi, '<span style="color:#d4af37;">warning</span>');
        }
        
        entry.appendChild(contentElement);
        
        if (terminalOutput) {
            terminalOutput.appendChild(entry);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    }
    
    // Add welcome message
    if (terminalOutput) {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        
        const welcomeMessage = `
        <div style="text-align:center;color:#cc0000;margin-bottom:15px;">
            <pre style="font-family:'Courier New',monospace;line-height:1.2;">
  ______ _____ _____ _____    _____ _____ _____ _____ _____ _____ 
 |  ____|  __ \\_   _|  __ \\  / ____|  __ \\_   _|  __ \\_   _|  __ \\
 | |__  | |__) || | | |  | || (___ | |__) || | | |  | || | | |__) |
 |  __| |  ___/ | | | |  | | \\___ \\|  ___/ | | | |  | || | |  _  / 
 | |    | |    _| |_| |__| | ____) | |    _| |_| |__| || |_| | \\ \\ 
 |_|    |_|   |_____|_____/ |_____/|_|   |_____|_____/_____|_|  \\_\\                                                                     
            </pre>
            <div style="font-family:'Courier New',monospace;font-size:1.2rem;margin-top:10px;">
                ★ FANCY SPIDER v3.1.8 ★
            </div>
            <div style="font-size:0.8rem;color:#989898;margin-top:5px;">
                Terminal access activated at ${hours}:${minutes}:${seconds}
            </div>
        </div>
        `;
        
        const welcomeEntry = document.createElement('div');
        welcomeEntry.className = 'terminal-entry';
        welcomeEntry.innerHTML = welcomeMessage;
        terminalOutput.appendChild(welcomeEntry);
        
        addTerminalEntry('info', 'System ready for operation. Select target and enter command...', 'SYSTEM');
    }
}

// Navigation helpers
function showTerminalTab(agentId) {
    showTab('terminal');
    
    // Set selected agent
    setTimeout(() => {
        const targetSelector = document.getElementById('terminal-target');
        if (targetSelector) {
            targetSelector.value = agentId;
        }
    }, 100);
}

function showAttackVectorsTab(agentId) {
    showTab('attack-vectors');
    
    // Set selected agent
    setTimeout(() => {
        const analysisSelector = document.getElementById('analysis-agent-select');
        if (analysisSelector) {
            analysisSelector.value = agentId;
            document.getElementById('analyze-btn').disabled = false;
        }
    }, 100);
}

// Soviet theme effects
function applySovietTheme() {
    // Add hammer and sickle watermark
    const watermark = document.createElement('div');
    watermark.className = 'soviet-watermark';
    watermark.innerHTML = '☭';
    document.body.appendChild(watermark);
    
    // Add scan line effect
    const scanLine = document.createElement('div');
    scanLine.className = 'scan-line';
    document.body.appendChild(scanLine);
    
    // Add stars to panel headers
    document.querySelectorAll('.panel-header h3').forEach(header => {
        if (!header.querySelector('.soviet-star')) {
            const star = document.createElement('span');
            star.className = 'soviet-star';
            star.innerHTML = ' ★';
            star.style.color = '#d4af37';
            star.style.marginLeft = '5px';
            header.appendChild(star);
        }
    });
    
    // Add Soviet-themed random terminal messages
    setInterval(() => {
        const terminalOutput = document.getElementById('terminal-output');
        if (terminalOutput && Math.random() < 0.05) { // 5% chance
            const sovietMessages = [
                "Connection established through secure relay...",
                "Checking target system integrity...",
                "Warning: Security system detected",
                "Connection encrypted using military-grade protocol",
                "Running counter-intelligence scan...",
                "Secure channel established",
                "Detecting active monitoring systems...",
                "Counter-measures activated",
                "Signal bounced through secure server",
                "Advanced connection protocols in use"
            ];
            
            const randomMessage = sovietMessages[Math.floor(Math.random() * sovietMessages.length)];
            
            const messageElement = document.createElement('div');
            messageElement.className = 'terminal-entry';
            messageElement.innerHTML = `
                <div class="entry-header">SYSTEM [${new Date().toTimeString().split(' ')[0]}]</div>
                <div class="entry-content" style="color: #cc0000;">
                    ★ ${randomMessage}
                </div>
            `;
            terminalOutput.appendChild(messageElement);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
            
            // Remove after a few seconds
            setTimeout(() => {
                if (messageElement.parentNode === terminalOutput) {
                    terminalOutput.removeChild(messageElement);
                }
            }, 5000);
        }
    }, 20000);
    
    // Add glitch effect to random elements
    setInterval(() => {
        const elements = document.querySelectorAll('.panel, .target-card, .btn.primary');
        if (elements.length > 0) {
            const randomEl = elements[Math.floor(Math.random() * elements.length)];
            const originalTransform = randomEl.style.transform || '';
            
            // Apply glitch
            randomEl.style.transform = `${originalTransform} translate(1px, 1px)`;
            randomEl.style.opacity = '0.8';
            
            // Reset after a short time
            setTimeout(() => {
                randomEl.style.transform = originalTransform;
                randomEl.style.opacity = '1';
            }, 150);
        }
    }, 3000);
    
    // Add custom terminal prompt
    const terminal = document.getElementById('terminal-output');
    if (terminal) {
        const prompt = document.createElement('div');
        prompt.className = 'terminal-prompt';
        prompt.innerHTML = `
            <span style="color: #cc0000;">fancy-spider@secure</span>:<span style="color: #d4af37;">~</span># <span class="cursor">▋</span>
        `;
        terminal.appendChild(prompt);
        
        // Blinking cursor effect
        const cursor = prompt.querySelector('.cursor');
        setInterval(() => {
            cursor.style.visibility = cursor.style.visibility === 'hidden' ? 'visible' : 'hidden';
        }, 500);
    }
    
    console.log('%c ★ FANCY SPIDER: ACTIVATED ★', 'color: #cc0000; font-weight: bold; font-size: 18px');
}
