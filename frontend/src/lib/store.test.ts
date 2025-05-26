import { useAuth } from './store';

describe('useAuth store', () => {
  it('sets and clears token and user', () => {
    const { setToken, setUser, logout } = useAuth.getState();
    setToken('test-token');
    setUser({ email: 'test@example.com', fullName: 'Test User' });
    expect(useAuth.getState().token).toBe('test-token');
    expect(useAuth.getState().user).toEqual({ email: 'test@example.com', fullName: 'Test User' });
    logout();
    expect(useAuth.getState().token).toBeNull();
    expect(useAuth.getState().user).toBeNull();
  });
});
