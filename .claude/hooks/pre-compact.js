#!/usr/bin/env node
/**
 * PreCompact Hook - Backup state before context compaction
 *
 * Triggered before Claude compacts context.
 * Creates a backup of important state to preserve across compaction.
 */

const fs = require('fs');
const path = require('path');

const stateDir = path.join(process.cwd(), '.claude', 'state');
const backupDir = path.join(stateDir, 'backups');

// Ensure backup directory exists
if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

// Files to backup
const filesToBackup = [
    'session_start.json',
    'file_changes.json',
    'active_agents.json',
    'prompts.json',
    'cost_tracking.json'
];

const backedUp = [];
const backupBundle = {};

for (const file of filesToBackup) {
    const sourcePath = path.join(stateDir, file);
    if (fs.existsSync(sourcePath)) {
        try {
            const content = fs.readFileSync(sourcePath, 'utf8');
            backupBundle[file] = JSON.parse(content);
            backedUp.push(file);
        } catch (e) {
            // Skip files that can't be read/parsed
        }
    }
}

// Write backup bundle
if (backedUp.length > 0) {
    const backupFile = path.join(backupDir, `pre-compact-${timestamp}.json`);
    fs.writeFileSync(backupFile, JSON.stringify({
        timestamp: new Date().toISOString(),
        files: backupBundle
    }, null, 2));

    // Clean up old backups (keep last 10)
    const backups = fs.readdirSync(backupDir)
        .filter(f => f.startsWith('pre-compact-'))
        .sort()
        .reverse();

    for (let i = 10; i < backups.length; i++) {
        try {
            fs.unlinkSync(path.join(backupDir, backups[i]));
        } catch (e) {
            // Ignore cleanup errors
        }
    }
}

// Log the backup
const logFile = path.join(process.cwd(), '.claude', 'session.log');
const logEntry = `[cs] ${new Date().toISOString().slice(0, 19)} PreCompact backup created: ${backedUp.length} files\n`;
try {
    fs.appendFileSync(logFile, logEntry);
} catch (e) {
    // Ignore
}

// Output
const output = {
    backedUp,
    timestamp,
    backupCount: backedUp.length
};

console.log(JSON.stringify(output));
