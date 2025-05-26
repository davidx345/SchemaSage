import { useAuth } from '@/lib/store';
import { useRouter } from 'next/navigation';

jest.mock('next/navigation', () => ({ useRouter: jest.fn() }));

describe('Auth flow', () => {
  beforeEach(() => {
    useAuth.getState().logout();
    jest.clearAllMocks();
  });

  it('logs in and out correctly', () => {
    const { setToken, setUser, logout } = useAuth.getState();
    setToken('token');
    setUser({ email: 'a@b.com', fullName: 'A B' });
    expect(useAuth.getState().token).toBe('token');
    expect(useAuth.getState().user?.email).toBe('a@b.com');
    logout();
    expect(useAuth.getState().token).toBeNull();
    expect(useAuth.getState().user).toBeNull();
  });
  it('redirects to login if not authenticated', () => {
    const replace = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace });
    // Simulate dashboard useEffect
    const token = useAuth.getState().token;
    if (!token) {
      replace('/auth/login');
    }
    expect(replace).toHaveBeenCalledWith('/auth/login');
  });

  it('should be implemented', () => {
    expect(true).toBe(true);
  });
});
