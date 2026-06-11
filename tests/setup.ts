import { beforeAll, afterAll } from 'vitest';

/**
 * Global test setup for Harness OS tests.
 *
 * Runs before all test files.
 * Sets up test environment variables and global mocks.
 */

beforeAll(() => {
  process.env.HARNESS_TEST_MODE = 'true';
  process.env.HARNESS_NON_INTERACTIVE = 'true';
  process.env.HARNESS_NO_COLOR = 'true';
});

afterAll(() => {
  delete process.env.HARNESS_TEST_MODE;
  delete process.env.HARNESS_NON_INTERACTIVE;
  delete process.env.HARNESS_NO_COLOR;
});
