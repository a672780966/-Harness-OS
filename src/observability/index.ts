import { HarnessEvent } from '../types.js';

export async function showReport(runId: string): Promise<void> {
  console.log(`Showing report: ${runId}`);
  // TODO: Read run report from .project/reports/runs/
}

export async function logEvent(event: Omit<HarnessEvent, 'eventId' | 'timestamp'>): Promise<void> {
  // TODO: Write event to .project/reports/events/<run-id>.jsonl
  console.log(`Event: ${event.type}`);
}
