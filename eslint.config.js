/**
 * Harness OS — ESLint Configuration
 *
 * Flat config (ESLint 9+) for TypeScript static analysis.
 * Low-risk baseline rules covering:
 *   - unused variables and imports
 *   - unhandled Promise issues
 *   - unsafe or dangerous TypeScript patterns
 *   - basic consistency checks
 *
 * Reference: HAR-07_REAL_LINT.md
 */

import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  // Global ignore patterns
  {
    ignores: ['dist/', 'node_modules/', 'coverage/', '*.config.*', '.*'],
  },

  // Base ESLint recommended rules
  eslint.configs.recommended,

  // TypeScript recommended rules
  ...tseslint.configs.recommended,

  // Project-specific overrides
  {
    languageOptions: {
      parserOptions: {
        project: './tsconfig.eslint.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // Unused variables (error in src, warn in tests)
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
      }],

      // Allow explicit any during development, warn in production
      '@typescript-eslint/no-explicit-any': 'warn',

      // Require explicit return types only for exported functions
      '@typescript-eslint/explicit-function-return-type': 'off',

      // No require imports (ESM project)
      '@typescript-eslint/no-require-imports': 'warn',

      // Prevent async function without await (low-priority warning)
      'require-await': 'warn',
      '@typescript-eslint/require-await': 'warn',

      // No empty promise bodies
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',

      // Prevent unused expressions (catches unreachable code)
      'no-unused-expressions': 'error',

      // Enforce === and !==
      'eqeqeq': ['error', 'always', { null: 'ignore' }],

      // No duplicate imports
      'no-duplicate-imports': 'error',

      // No console.log in production code (allow in specific files)
      'no-console': 'warn',
    },
  },

  // Test files: relaxed rules
  {
    files: ['tests/**/*.ts'],
    rules: {
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': 'off',
      'require-await': 'off',
      '@typescript-eslint/require-await': 'off',
    },
  },
);
