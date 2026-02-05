#!/usr/bin/env node
/**
 * UserPromptSubmit Hook - Enhanced context injection
 *
 * Triggered when user submits a prompt.
 * Injects relevant context based on prompt content.
 */

const fs = require('fs');
const path = require('path');

const stateDir = path.join(process.cwd(), '.claude', 'state');
const logFile = path.join(process.cwd(), '.claude', 'session.log');

// Ensure state directory exists
if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
}

// Get current timestamp
const timestamp = new Date().toISOString();

// Log the prompt submission
const logEntry = `[cs] ${timestamp.slice(0, 19)} Prompt received\n`;
fs.appendFileSync(logFile, logEntry);

// Read prompt from stdin if available (hook receives tool input)
let promptText = '';
try {
    const input = process.env.HOOK_INPUT;
    if (input) {
        const parsed = JSON.parse(input);
        promptText = parsed.prompt || parsed.content || '';
    }
} catch (e) {
    // No input available
}

// Detect keywords for rule loading
const keywords = {
    auth: ['auth', 'login', 'jwt', 'oauth', 'session', 'password', 'token', 'credential'],
    test: ['test', 'coverage', 'mock', 'spec', 'unittest', 'pytest', 'vitest', 'jest'],
    api: ['api', 'endpoint', 'rest', 'graphql', 'route', 'http', 'request', 'response'],
    database: ['database', 'query', 'sql', 'orm', 'migration', 'schema', 'table', 'model'],
    performance: ['performance', 'cache', 'optimize', 'speed', 'slow', 'fast', 'memory', 'latency'],
    ui: ['ui', 'component', 'css', 'style', 'layout', 'design', 'theme', 'color', 'responsive'],
    security: ['security', 'vulnerability', 'xss', 'injection', 'sanitize', 'encrypt', 'hash', 'secret'],
    codeQuality: ['lint', 'format', 'refactor', 'clean', 'organize', 'style', 'convention', 'typing'],
    errorHandling: ['error', 'bug', 'fix', 'exception', 'catch', 'throw', 'handle', 'crash'],
    documentation: ['doc', 'readme', 'comment', 'docstring', 'explain', 'document']
};

const promptLower = promptText.toLowerCase();
const detectedTopics = [];

for (const [topic, words] of Object.entries(keywords)) {
    if (words.some(word => promptLower.includes(word))) {
        detectedTopics.push(topic);
    }
}

// Track prompt metadata
const promptMeta = {
    timestamp,
    topics: detectedTopics,
    length: promptText.length
};

// Save to state for later analysis
const promptsFile = path.join(stateDir, 'prompts.json');
let prompts = [];
if (fs.existsSync(promptsFile)) {
    try {
        prompts = JSON.parse(fs.readFileSync(promptsFile, 'utf8'));
    } catch (e) {
        prompts = [];
    }
}
prompts.push(promptMeta);
// Keep only last 50 prompts
if (prompts.length > 50) {
    prompts = prompts.slice(-50);
}
fs.writeFileSync(promptsFile, JSON.stringify(prompts, null, 2));

// Output (continue execution)
const output = {
    continue: true,
    detectedTopics
};

console.log(JSON.stringify(output));
