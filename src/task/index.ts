import { TaskState, TaskType } from '../types.js';

export async function runTask(task: string, options?: { json?: boolean; quiet?: boolean }): Promise<void> {
  console.log(`Running task: ${task}`);
  // TODO: Full task lifecycle per 06_TASK_DECISION_PROJECT_MANAGER.md §7
  // 1. Normalize task
  // 2. Create task record
  // 3. Build Context Pack (context/)
  // 4. Start Codex run
  // 5. Monitor execution
  // 6. Run verification
  // 7. Generate report
}

export async function resumeRun(runId: string): Promise<void> {
  console.log(`Resuming run: ${runId}`);
  // TODO: Read run state, restore checkpoint, continue execution
}
