export async function listDecisions(): Promise<void> {
  console.log('Listing decisions');
  // TODO: Read .project/decisions/ and display ADR list
}

export async function proposeDecision(): Promise<void> {
  console.log('Proposing new decision');
  // TODO: Create ADR with template, write to .project/decisions/
}

export async function acceptDecision(decisionId: string): Promise<void> {
  console.log(`Accepting decision: ${decisionId}`);
  // TODO: Validate decision, check governance, update status
}
