import { projectApi } from './api';

describe('projectApi', () => {
  it('should have getProjects and createProject methods', () => {
    expect(typeof projectApi.getProjects).toBe('function');
    expect(typeof projectApi.createProject).toBe('function');
  });
});
