import { NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  // handleProxyRequest is designed to handle FormData if the Content-Type is multipart/form-data
  return handleProxyRequest({
    method: 'POST',
    backendPath: '/api/schema/detect-from-file',
    request: req,
  });
}
