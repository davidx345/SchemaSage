module.exports = {
  preset: 'ts-jest/presets/js-with-babel',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { 
      useESM: true,
      babelConfig: true, // Add this line
    }],
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/src/jest-setup.ts'],
  transformIgnorePatterns: [
    '/node_modules/'
  ],
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  globals: {}, // Remove deprecated ts-jest config
};
