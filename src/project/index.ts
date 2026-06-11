import { ProjectManifest } from '../types.js';

const PROJECT_DIR = '.project';
const STATE_DIR = `${PROJECT_DIR}/state`;
const TASKS_DIR = `${PROJECT_DIR}/tasks`;
const DECISIONS_DIR = `${PROJECT_DIR}/decisions`;
const REPORTS_DIR = `${PROJECT_DIR}/reports`;
const CONTEXT_DIR = `${PROJECT_DIR}/context`;

export async function createProject(name: string): Promise<void> {
  console.log(`Creating project: ${name}`);
  // TODO: Implement full project creation flow per 06_TASK_DECISION_PROJECT_MANAGER.md
  // 1. Create project directory
  // 2. Initialize Git repo
  // 3. Inject AGENTS.md template
  // 4. Create .project/ structure
  // 5. Generate manifest.json
  // 6. Create initial checkpoint
}

export async function openProject(path: string): Promise<void> {
  console.log(`Opening project: ${path}`);
  // TODO: Validate repo, read AGENTS.md, check .project/, repair if needed
}

export async function initProject(): Promise<void> {
  console.log('Initializing Harness OS in current project');
  // TODO: Create .project/ structure in existing project
}

export async function repairProject(): Promise<void> {
  console.log('Repairing project structure');
  // TODO: Fix missing directories, validate manifest, refresh repo map
}
