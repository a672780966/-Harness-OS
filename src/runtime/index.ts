export async function showStatus(): Promise<void> {
  console.log('Showing project status');
  // TODO: Read active run, task state, git status
}

export async function showConfig(options?: { json?: boolean }): Promise<void> {
  console.log('Showing config');
  // TODO: Load and display effective config
}
