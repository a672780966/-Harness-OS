import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    // Global test configuration
    globals: true,
    environment: 'node',

    // Test file patterns
    include: ['tests/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],

    // Timeouts
    testTimeout: 30_000,
    hookTimeout: 30_000,

    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      include: ['src/**/*.ts'],
      exclude: ['src/cli/index.ts', 'src/types.ts'],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },

    // Setup file
    setupFiles: ['./tests/setup.ts'],

    // TypeScript
    typecheck: {
      tsconfig: './tsconfig.json',
      include: ['tests/**/*.test.ts'],
    },

    // Sequential for integration/E2E tests that share state
    fileParallelism: true,
    maxConcurrency: 4,
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
