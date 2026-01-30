# Claude Math Reasoning Prompts

Source: https://github.com/langgptai/awesome-claude-prompts

## MetaPrompt (Official Anthropic Example)

This is Anthropic's official meta-prompt for structured reasoning:

```
You are an expert at structured reasoning. When given a task:

1. First, understand what is being asked
2. Break down the problem into clear steps
3. Work through each step systematically
4. Verify your reasoning at each stage
5. Provide the final answer concisely

For mathematical problems:
- Show your work clearly
- State any assumptions you make
- Verify calculations when possible
- Use appropriate mathematical notation
```

## Step-by-Step Math Reasoning Pattern

```
When solving mathematical problems, follow this pattern:

<thinking>
1. Identify the problem type and relevant concepts
2. Outline the solution approach
3. List any formulas or theorems needed
</thinking>

<working>
Step 1: [Initial setup/known values]
Step 2: [Apply formula/method]
Step 3: [Calculate intermediate results]
Step 4: [Verify each step]
</working>

<answer>
[Final answer with units if applicable]
</answer>
```

## Extended Thinking Mode (Claude 3.7 Sonnet)

Claude 3.7 Sonnet has a reasoning/extended thinking mode that:
- Allows internal deliberation before responding
- Enables step-by-step mathematical reasoning
- Useful for complex calculations and proofs
- Can be toggled on/off based on problem complexity

## Concise Math Response Pattern

Following Claude Code principles for math:

```
For simple calculations:
- Provide the answer directly
- Minimal explanation unless asked
- One-line responses preferred

For complex problems:
- Brief setup of approach
- Key steps only
- Final answer clearly marked
```

## Mathematical Proof Structure

```
When asked to prove something:

1. State the theorem/claim
2. Identify proof technique (direct, contradiction, induction, etc.)
3. Show each logical step
4. Conclude with QED or clear statement of completion
```

## Error Checking Pattern

```
After solving:
- Verify units match
- Check order of magnitude is reasonable
- Substitute answer back if possible
- Identify any potential edge cases
```

## Applications for RALF

These patterns can be incorporated into RALF for:
- Task complexity estimation
- Step-by-step implementation planning
- Verification of technical decisions
- Breaking down complex features
