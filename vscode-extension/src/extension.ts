import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as cp from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "portable-agent-protocol" is now active!');

    // Command: Initialize Workspace
    let initDisposable = vscode.commands.registerCommand('pap.initWorkspace', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('Please open a folder to initialize PAP workspace.');
            return;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;
        const agentDir = path.join(rootPath, '.agent');

        try {
            if (!fs.existsSync(agentDir)) {
                fs.mkdirSync(agentDir);
            }
            ['skills', 'prompts', 'workflows', 'memory'].forEach(dir => {
                const p = path.join(agentDir, dir);
                if (!fs.existsSync(p)) fs.mkdirSync(p);
            });

            const agentMd = path.join(agentDir, 'agent.md');
            if (!fs.existsSync(agentMd)) {
                fs.writeFileSync(agentMd, 
`---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: new-agent
version: "0.1.0"
purpose: Define the core purpose of this agent here.
language: en-US
authorization_level: interactive-approval
use_case_tags: [default-agent]
tools: []
mcp_servers: {}
---

# Agent Manifest
`
                );
            }

            const skillTemplate = path.join(agentDir, 'skills', '_template.md');
            if (!fs.existsSync(skillTemplate)) {
                fs.writeFileSync(skillTemplate, 
`---
name: "{{skill_name}}"
description: "{{short_description_under_50_chars}}"
version: "1.0.0"
author: "{{author_or_ai_generator}}"
---

# {{skill_name}}

## 1. Purpose
{{purpose_description}}

## 2. Required Inputs
- \`{{param_1_name}}\` ({{type}}, **Required**): {{param_1_description}}

## 3. Expected Outputs
- **Success Format**: {{success_format_description}}

## 4. Execution Boundaries & Safety
> [!WARNING]
> **Safety Constraints:**
> - {{constraint_1}}

## 5. Fallback Mechanism
- **If {{error_condition_1}}**: {{fallback_action_1}}
`
                );
            }

            const personaTemplate = path.join(agentDir, 'persona_template.md');
            if (!fs.existsSync(personaTemplate)) {
                fs.writeFileSync(personaTemplate, 
`# PAP Persona Definition Template

## 1. Core Identity & Tone
- **Role**: {{agent_role}}
- **Tone of Voice**: {{tone_description}}
- **Language**: {{language_from_manifest}}

## 2. Prime Directives
1. {{directive_1}}

## 3. Avoidance Rules
- **DO NOT**: {{avoidance_1}}

## 4. Default Workflow
1. {{step_1}}
`
                );
            }

            vscode.window.showInformationMessage('PAP Workspace successfully initialized!');
            
            // Open agent.md
            const doc = await vscode.workspace.openTextDocument(agentMd);
            await vscode.window.showTextDocument(doc);
            
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to initialize PAP: ${error.message}`);
        }
    });

    // Command: Sync MCP Servers
    let syncDisposable = vscode.commands.registerCommand('pap.mcpSync', () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open.');
            return;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;
        const cliPath = path.join(rootPath, 'cli.py');
        
        if (!fs.existsSync(cliPath)) {
            vscode.window.showErrorMessage('Could not find cli.py in the workspace root. Ensure you are in the PAP runtime repository.');
            return;
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Syncing MCP Servers...",
            cancellable: false
        }, async (progress) => {
            return new Promise<void>((resolve, reject) => {
                cp.exec('python cli.py mcp sync', { cwd: rootPath }, (error, stdout, stderr) => {
                    if (error) {
                        vscode.window.showErrorMessage(`MCP Sync failed: ${stderr}`);
                        reject(error);
                    } else {
                        vscode.window.showInformationMessage('MCP Servers synced successfully!');
                        resolve();
                    }
                });
            });
        });
    });

    context.subscriptions.push(initDisposable);
    context.subscriptions.push(syncDisposable);
}

export function deactivate() {}
