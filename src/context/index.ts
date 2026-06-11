import { ContextPack } from '../types.js';

export async function buildContext(input: {
  projectId: string;
  taskId: string;
  runId: string;
  userInstruction: string;
  workspacePath: string;
  maxTokens?: number;
}): Promise<ContextPack> {
  console.log(`Building context for task: ${input.taskId}`);
  // TODO: Full Context Engineering flow per 05_CONTEXT_ENGINEERING.md
  // 1. Load AGENTS.md
  // 2. Load project state
  // 3. Inspect git state
  // 4. Discover relevant files
  // 5. Build Context Pack
  // 6. Apply budget
  // 7. Save snapshot
  throw new Error('Not implemented');
}
