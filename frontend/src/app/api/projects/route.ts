import { NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function GET(req: NextRequest) {
  return handleProxyRequest({ method: 'GET', backendPath: '/api/database/projects', request: req });
}

export async function POST(req: NextRequest) {
  return handleProxyRequest({ method: 'POST', backendPath: '/api/database/projects', request: req });
}