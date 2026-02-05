#!/usr/bin/env node
/**
 * SessionEnd Hook - Archive session and update STATUS.md
 *
 * Triggered when a Claude Code session ends.
 * Archives session state and optionally updates STATUS.md.
 */

const fs = require('fs');
const path = require('path');

const stateDir = path.join(process.cwd(), '.claude', 'state');
const sessionFile = path.join(stateDir, 'session_start.json');
const archiveDir = path.join(stateDir, 'archive');

// Ensure archive directory exists
if (!fs.existsSync(archiveDir)) {
    fs.mkdirSync(archiveDir, { recursive: true });
}

// Read session start info
let sessionInfo = {};
if (fs.existsSync(sessionFile)) {
    try {
        sessionInfo = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
    } catch (e) {
        sessionInfo = { id: 'unknown', timestamp: new Date().toISOString() };
    }
}

// Calculate session duration
const startTime = sessionInfo.timestamp ? new Date(sessionInfo.timestamp) : new Date();
const endTime = new Date();
const durationMs = endTime - startTime;
const durationMin = Math.round(durationMs / 60000);

// Read file changes if tracked
const changesFile = path.join(stateDir, 'file_changes.json');
let fileChanges = [];
if (fs.existsSync(changesFile)) {
    try {
        fileChanges = JSON.parse(fs.readFileSync(changesFile, 'utf8'));
    } catch (e) {
        // Ignore
    }
}

// Create session archive
const sessionEnd = {
    ...sessionInfo,
    endTimestamp: endTime.toISOString(),
    durationMinutes: durationMin,
    filesChanged: fileChanges.length,
    filesList: fileChanges
};

// Archive the session
const archiveFile = path.join(archiveDir, `${sessionInfo.id || 'session'}.json`);
fs.writeFileSync(archiveFile, JSON.stringify(sessionEnd, null, 2));

// Clean up current session files
if (fs.existsSync(sessionFile)) {
    fs.unlinkSync(sessionFile);
}
if (fs.existsSync(changesFile)) {
    fs.unlinkSync(changesFile);
}

// Append to session log
const logFile = path.join(process.cwd(), '.claude', 'session.log');
const logEntry = `[cs] ${endTime.toISOString().slice(0, 19)} SessionEnd id=${sessionInfo.id || 'unknown'} duration=${durationMin}min files=${fileChanges.length}\n`;
fs.appendFileSync(logFile, logEntry);

// Output summary
const output = {
    sessionId: sessionInfo.id,
    duration: `${durationMin} minutes`,
    filesChanged: fileChanges.length,
    archived: archiveFile
};

console.log(JSON.stringify(output));
