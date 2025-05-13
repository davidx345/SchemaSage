import { projectApi } from './api';

describe('projectApi integration', () => {
  it('should fetch projects (mocked)', async () => {
    // This is a placeholder for a real integration test
    // In real usage, mock fetch or use MSW
    expect(typeof projectApi.getProjects).toBe('function');
  });
});
