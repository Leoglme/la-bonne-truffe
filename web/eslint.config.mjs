// @ts-check
import eslintConfigPrettier from 'eslint-config-prettier'
import eslintPluginJSDoc from 'eslint-plugin-jsdoc'
import eslintPluginPrettier from 'eslint-plugin-prettier'
import eslintPluginUnusedImports from 'eslint-plugin-unused-imports'
import eslintPluginTypeScript from '@typescript-eslint/eslint-plugin'
import withNuxt from './.nuxt/eslint.config.mjs'

const typedefOptions = {
  arrayDestructuring: true,
  arrowParameter: true,
  memberVariableDeclaration: true,
  objectDestructuring: true,
  parameter: true,
  propertyDeclaration: true,
  variableDeclaration: true,
  variableDeclarationIgnoreFunction: false,
}

export default withNuxt(
  {
    name: 'la-bonne-truffe/ignores',
    ignores: [
      'dist',
      '.output',
      'node_modules',
      '.nuxt',
      '.nuxt-typecheck',
      'src-tauri/target',
      'src-tauri/gen',
      'public/sw.js',
      'app/types/api.generated.ts',
    ],
  },
  eslintPluginJSDoc.configs['flat/recommended'],
  {
    plugins: {
      'unused-imports': eslintPluginUnusedImports,
      prettier: eslintPluginPrettier,
      '@typescript-eslint': eslintPluginTypeScript,
    },
    settings: {
      jsdoc: {
        mode: 'typescript',
      },
    },
    rules: {
      // Types are carried by TypeScript, never by JSDoc tags — these would ask for `@param {string}`.
      'jsdoc/require-param-type': 'off',
      'jsdoc/require-returns-type': 'off',
      'jsdoc/require-throws-type': 'off',
      'jsdoc/no-undefined-types': 'off',
      'jsdoc/reject-any-type': 'off',
      'jsdoc/tag-lines': 'off',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-extraneous-class': ['error', { allowStaticOnly: true }],
      '@typescript-eslint/explicit-function-return-type': ['error'],
      '@typescript-eslint/typedef': ['error', typedefOptions],
      '@typescript-eslint/no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
      'vue/no-multiple-template-root': 'off',
      'vue/component-name-in-template-casing': ['error', 'PascalCase', { registeredComponentsOnly: false }],
      'vue/block-order': [
        'error',
        {
          order: ['template', 'script', 'style'],
        },
      ],
      'prettier/prettier': 'error',
      'jsdoc/require-jsdoc': [
        'error',
        {
          require: {
            FunctionDeclaration: true,
            MethodDefinition: true,
            ArrowFunctionExpression: false,
            FunctionExpression: true,
          },
        },
      ],
    },
  },
  {
    files: ['**/*.vue'],
    rules: {
      'jsdoc/require-param': 'off',
      'jsdoc/require-returns': 'off',
      'jsdoc/require-param-description': 'off',
      'jsdoc/require-returns-description': 'off',
    },
  },
  {
    files: ['app/composables/**/*.ts', 'app/services/**/*.ts', 'app/stores/**/*.ts'],
    rules: {
      'jsdoc/require-param': 'off',
      'jsdoc/require-returns': 'off',
      'jsdoc/require-param-description': 'off',
      'jsdoc/check-param-names': 'off',
    },
  },
  {
    files: ['app/stores/**/*.ts'],
    rules: {
      // Pinia has no type that can be written for a setup store: `export const useXStore = defineStore(…)` stays bare.
      '@typescript-eslint/typedef': ['error', { ...typedefOptions, variableDeclaration: false }],
    },
  },
  {
    // JavaScript tooling scripts cannot carry type annotations.
    files: ['**/*.mjs', '**/*.js'],
    rules: {
      '@typescript-eslint/typedef': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off',
    },
  },
  eslintConfigPrettier,
)
