/**
 * Athena VS Code/Cursor Adapter
 * Ultra-thin adapter that forwards to athena-devd
 */
import fetch from 'node-fetch';
import * as vscode from 'vscode';

const ATHENA_URL = 'http://localhost:8765';

export function activate(context: vscode.ExtensionContext) {
    console.log('Athena copilot adapter activated');
    
    // Register command: "Athena: Explain & Fix"
    let explainCommand = vscode.commands.registerCommand('athena.explainAndFix', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        
        // Gather context
        const document = editor.document;
        const selection = editor.selection;
        const diagnostics = vscode.languages.getDiagnostics(document.uri);
        const visibleEditors = vscode.window.visibleTextEditors.map(e => e.document.fileName);
        
        // Build request
        const request = {
            repoRoot: vscode.workspace.workspaceFolders?.[0].uri.fsPath || '',
            file: document.fileName,
            cursor: {
                line: selection.active.line,
                col: selection.active.character
            },
            selection: selection.isEmpty ? null : {
                start: selection.start.line,
                end: selection.end.line
            },
            visibleFiles: visibleEditors,
            diagnostics: diagnostics.map(d => ({
                file: document.fileName,
                line: d.range.start.line,
                msg: d.message,
                severity: d.severity
            })),
            intent: 'explain-and-fix',
            query: selection.isEmpty ? null : document.getText(selection)
        };
        
        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Athena is thinking...",
            cancellable: false
        }, async (progress) => {
            try {
                // Call Athena
                const response = await fetch(`${ATHENA_URL}/assist`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(request)
                });
                
                if (!response.ok) {
                    throw new Error(`Athena error: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Show result in new panel
                const panel = vscode.window.createWebviewPanel(
                    'athenaResult',
                    'Athena Answer',
                    vscode.ViewColumn.Beside,
                    {enableScripts: true}
                );
                
                // Format citations as clickable links
                const citationsHtml = result.citations.map((cite: string) => {
                    const [path, range] = cite.split(':');
                    return `<a href="vscode://file/${path}?line=${range.split('-')[0]}">${cite}</a>`;
                }).join('<br/>');
                
                panel.webview.html = `
                    <!DOCTYPE html>
                    <html>
                    <head><style>
                        body { font-family: system-ui; padding: 20px; }
                        pre { background: #f5f5f5; padding: 10px; border-radius: 4px; }
                        .citations { margin-top: 20px; font-size: 12px; color: #666; }
                    </style></head>
                    <body>
                        <h2>Athena's Answer:</h2>
                        <pre>${escapeHtml(result.summary)}</pre>
                        <div class="citations">
                            <strong>Citations:</strong><br/>
                            ${citationsHtml}
                        </div>
                    </body>
                    </html>
                `;
                
                vscode.window.showInformationMessage('Athena answered!');
                
            } catch (error) {
                vscode.window.showErrorMessage(`Athena error: ${error}`);
            }
        });
    });
    
    context.subscriptions.push(explainCommand);
    
    // Check if daemon is running
    fetch(`${ATHENA_URL}/healthz`).then(r => {
        if (r.ok) {
            vscode.window.showInformationMessage('Athena copilot ready!');
        }
    }).catch(() => {
        vscode.window.showWarningMessage('Athena daemon not running. Start with: make athena-up');
    });
}

function escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&#039;');
}

export function deactivate() {}

