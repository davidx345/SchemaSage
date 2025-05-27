import { NextRequest, NextResponse } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  try {
    const originalBody = await req.json();
    const { data, options } = originalBody;

    // Backend expects { data, settings: options }
    const modifiedBody = { 
      data,
      settings: options 
    };

    const modifiedRequest = new NextRequest(req.nextUrl.clone(), {
      method: 'POST',
      headers: req.headers,
      body: JSON.stringify(modifiedBody),
      duplex: 'half' // Required for NextRequest with body
    });

    // Assuming handleProxyRequest expects the endpoint as a property of the request
    // (modifiedRequest as NextRequest & { endpoint: string }).endpoint = '/api/schema/detect';
    return handleProxyRequest({
      backendPath: '/api/schema/detect',
      request: modifiedRequest,
      method: 'POST'
    });
  } catch (error) {
    console.error('Schema detection error:', error);
    const message = error instanceof Error ? error.message : 'Internal server error during request modification';
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}