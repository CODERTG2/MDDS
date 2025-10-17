import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

class MCPClientManager {
    constructor() {
        this.client = null;
        this.isConnected = false;
    }

    async initialize() {
        try {
            const transport = new StdioClientTransport({
                command: '.venv/bin/python',
                args: ['src/MCPServer.py']
            });
            
            this.client = new Client(
                {
                    name: "mdds-client",
                    version: "1.0.0"
                },
                {
                    capabilities: {}
                }
            );
            
            await this.client.connect(transport);
            this.isConnected = true;
            console.log('MCP client connected successfully');
        } catch (error) {
            console.error('Failed to connect MCP client:', error);
            throw error;
        }
    }

    async callTool(toolRequest) {
        if (!this.isConnected) {
            throw new Error('MCP client not connected');
        }
        
        try {
            const result = await this.client.callTool({
                name: toolRequest.name,
                arguments: toolRequest.arguments || {}
            });
            return result;
        } catch (error) {
            console.error('Tool call failed:', error);
            throw error;
        }
    }

    async listTools() {
        if (!this.isConnected) {
            throw new Error('MCP client not connected');
        }
        
        return await this.client.listTools();
    }

    async disconnect() {
        if (this.isConnected && this.client) {
            await this.client.close();
            this.isConnected = false;
        }
    }
}

export const mcpClient = new MCPClientManager();