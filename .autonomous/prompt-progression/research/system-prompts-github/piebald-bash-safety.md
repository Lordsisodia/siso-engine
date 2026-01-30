# Bash Command Safety - Prefix Detection

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Purpose

System prompt for detecting command prefixes and command injection in Bash tool usage.

## Policy Specification

This document defines risk levels for actions that the Claude Code agent may take. This classification system is part of a broader safety framework and is used to determine when additional user confirmation or oversight may be needed.

## Definitions

**Command Injection:** Any technique used that would result in a command being run other than the detected prefix.

## Command Prefix Extraction

The system includes examples section with various command prefix patterns and command injection detection rules.

## Task

The user has allowed certain command prefixes to be run, and will otherwise be asked to approve or deny the command.

Your task is to determine the command prefix for the following command. The prefix must be a string prefix of the full command.

## Safety Rules

**IMPORTANT:** Bash commands may run multiple commands that are chained together.

For safety, if the command seems to contain command injection, you must return `command_injection_detected`.

This will help protect the user: if they think that they're allowlisting command A, but the AI coding agent sends a malicious command that technically has the same prefix as command A, then the safety system will see that you said `command_injection_detected` and ask the user for manual confirmation.

Note that not every command has a prefix. If a command has no prefix, return `none`.

## Output Format

ONLY return the prefix. Do not return any other text, markdown markers, or other content or formatting.

## RALF Relevance

Critical safety pattern for RALF's Bash tool usage:
- Command injection detection
- Prefix-based allowlisting
- Explicit safety returns
- No extra output formatting
