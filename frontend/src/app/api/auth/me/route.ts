import { NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function GET(req: NextRequest) {
  return handleProxyRequest({
    method: 'GET',
    backendPath: '/api/auth/me',
    request: req,
  });
}
