#!/usr/bin/env node
/**
 * Assistant Broker Node.js Client
 * Minimal, production-ready client for broker API
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

class BrokerClient {
  constructor(baseUrl = 'http://127.0.0.1:8080', token = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    
    // Get token from env or file
    if (token) {
      this.token = token;
    } else if (process.env.ASSISTANT_BROKER_TOKEN) {
      this.token = process.env.ASSISTANT_BROKER_TOKEN;
    } else {
      const tokenPath = path.join(os.homedir(), '.assistant-broker-token');
      if (fs.existsSync(tokenPath)) {
        this.token = fs.readFileSync(tokenPath, 'utf8').trim();
      } else {
        throw new Error(
          'No token found. Set ASSISTANT_BROKER_TOKEN env var ' +
          'or create ~/.assistant-broker-token'
        );
      }
    }
    
    this.headers = {
      'Content-Type': 'application/json',
      'X-Assistant-Token': this.token
    };
  }
  
  async _request(endpoint, data) {
    const url = `${this.baseUrl}/${endpoint.replace(/^\//, '')}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.reason || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  async health() {
    const response = await fetch(`${this.baseUrl}/v1/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  
  async openApp(bundleId) {
    return this._request('v1/open_app', { bundle_id: bundleId });
  }
  
  async quitApp(bundleId, force = false) {
    return this._request('v1/quit_app', { bundle_id: bundleId, force });
  }
  
  async runCommand(cmd, args) {
    return this._request('v1/run', { cmd, args });
  }
  
  async writeFile(filePath, content) {
    return this._request('v1/write_file', { path: filePath, content });
  }
  
  async readFile(filePath) {
    const result = await this._request('v1/read_file', { path: filePath });
    return result.content || '';
  }
  
  async revealInFinder(filePath) {
    return this.runCommand('open', ['-R', filePath]);
  }
  
  async openPath(filePath) {
    return this.runCommand('open', [filePath]);
  }
}

// Convenience functions
function getClient() {
  return new BrokerClient();
}

async function openApp(bundleId) {
  await getClient().openApp(bundleId);
}

async function reveal(filePath) {
  await getClient().revealInFinder(filePath);
}

// Demo if run directly
if (require.main === module) {
  (async () => {
    const client = new BrokerClient();
    
    console.log('✅ Health check:', await client.health());
    console.log('\n📝 Opening Calculator...');
    await client.openApp('com.apple.calculator');
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    console.log('❌ Closing Calculator...');
    await client.quitApp('com.apple.calculator');
    
    console.log('\n✅ Demo complete!');
  })().catch(console.error);
}

module.exports = { BrokerClient, getClient, openApp, reveal };

