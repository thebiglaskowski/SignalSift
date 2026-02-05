#!/usr/bin/env node
/**
 * Shared utilities for Claude Sentient hooks
 *
 * Provides common functionality used across multiple hooks:
 * - State directory management
 * - Hook input parsing
 * - JSON file I/O
 * - Logging
 */

const fs = require('fs');
const path = require('path');

/**
 * Ensure the .claude/state directory exists
 * @returns {string} Path to the state directory
 */
function ensureStateDir() {
    const stateDir = path.join(process.cwd(), '.claude', 'state');
    if (!fs.existsSync(stateDir)) {
        fs.mkdirSync(stateDir, { recursive: true });
    }
    return stateDir;
}

/**
 * Parse hook input from environment variable or stdin
 * @returns {Object} Parsed input object or empty object if parsing fails
 */
function parseHookInput() {
    try {
        const input = process.env.HOOK_INPUT;
        if (input) {
            return JSON.parse(input);
        }
    } catch (e) {
        // Fall through to stdin
    }

    try {
        const stdin = fs.readFileSync(0, 'utf8');
        return JSON.parse(stdin);
    } catch (e) {
        return {};
    }
}

/**
 * Load JSON data from a file
 * @param {string} filePath - Path to the JSON file
 * @param {Object} defaultValue - Default value if file doesn't exist or is invalid
 * @returns {Object} Parsed JSON or default value
 */
function loadJsonFile(filePath, defaultValue = {}) {
    if (!fs.existsSync(filePath)) {
        return defaultValue;
    }
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
        return defaultValue;
    }
}

/**
 * Save JSON data to a file
 * @param {string} filePath - Path to the JSON file
 * @param {Object} data - Data to save
 * @returns {boolean} True if successful, false otherwise
 */
function saveJsonFile(filePath, data) {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * Log a message to the session log file
 * @param {string} message - Message to log
 * @param {string} level - Log level (INFO, WARNING, ERROR, BLOCKED)
 */
function logMessage(message, level = 'INFO') {
    const logFile = path.join(process.cwd(), '.claude', 'session.log');
    const timestamp = new Date().toISOString().slice(0, 19);
    const logEntry = `[cs] ${timestamp} ${level}: ${message}\n`;
    try {
        fs.appendFileSync(logFile, logEntry);
    } catch (e) {
        // Ignore log errors
    }
}

/**
 * Get the path to a state file
 * @param {string} filename - Name of the state file
 * @returns {string} Full path to the state file
 */
function getStateFilePath(filename) {
    return path.join(ensureStateDir(), filename);
}

/**
 * Load state from a named state file
 * @param {string} filename - Name of the state file (without path)
 * @param {Object} defaultValue - Default value if file doesn't exist
 * @returns {Object} State data or default value
 */
function loadState(filename, defaultValue = {}) {
    return loadJsonFile(getStateFilePath(filename), defaultValue);
}

/**
 * Save state to a named state file
 * @param {string} filename - Name of the state file (without path)
 * @param {Object} data - State data to save
 * @returns {boolean} True if successful
 */
function saveState(filename, data) {
    ensureStateDir();
    return saveJsonFile(getStateFilePath(filename), data);
}

module.exports = {
    ensureStateDir,
    parseHookInput,
    loadJsonFile,
    saveJsonFile,
    logMessage,
    getStateFilePath,
    loadState,
    saveState,
};
