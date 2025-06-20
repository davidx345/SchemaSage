import { NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

// Updated route parameter type to match Next.js 15.3.2 expectations
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  const { projectId } = await params;
  return handleProxyRequest({ method: 'GET', backendPath: `/api/database/projects/${projectId}`, request: req });
}

// PUT handler with inline type definition
export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  const { projectId } = await params;
  return handleProxyRequest({ method: 'PUT', backendPath: `/api/database/projects/${projectId}`, request: req });
}

// DELETE handler with inline type definition
export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  const { projectId } = await params;
  return handleProxyRequest({ method: 'DELETE', backendPath: `/api/database/projects/${projectId}`, request: req });
}