import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { mcpClient } from './MCPClientManager.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

async function startServer() {
    try {
        await mcpClient.initialize();
        console.log('MCP client connected successfully');

        app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'public', 'index.html'));
        });

        app.post('/api/mcp', async (req, res) => {
            try {
                const result = await mcpClient.callTool(req.body);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        app.listen(PORT, () => {
            console.log(`Server running on http://localhost:${PORT}`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer();