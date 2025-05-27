import { NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  return handleProxyRequest({
    method: 'POST',
    backendPath: '/api/auth/login',
    request: req,
  });
}
