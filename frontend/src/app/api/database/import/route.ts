import { NextRequest } from 'next/server';
// API_BASE_URL is used by handleProxyRequest.
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  // The request body (containing database configuration) will be read and proxied by handleProxyRequest.
  return handleProxyRequest({
    method: 'POST',
    backendPath: '/api/database/import',
    request: req,
  });
}