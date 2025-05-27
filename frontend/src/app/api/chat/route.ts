import { NextResponse, NextRequest } from 'next/server';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  try {
    const originalBody = await req.json();
    const { messages, context } = originalBody;
    
    const schema_data = context?.schema;
    
    if (!schema_data) {
      return NextResponse.json(
        { success: false, message: 'Schema data is required for chat' },
        { status: 400 }
      );
    }

    // Restructure request to match backend's expected format
    const backendRequestBody = {
      schema_data: schema_data,
      messages: messages.map((msg: {role: string; content: string}) => ({
        role: msg.role,
        content: msg.content
      }))
    };

    const modifiedRequest = new NextRequest(req.url, {
        method: req.method,
        headers: req.headers, // Pass original headers
        body: JSON.stringify(backendRequestBody),
        duplex: 'half' // Required for ReadableStream body in some environments
    });

    return handleProxyRequest({
      method: 'POST',
      backendPath: '/api/schema/chat',
      request: modifiedRequest, // Pass the new request with the transformed body
    });

  } catch (error) {
    console.error('Chat error in route handler:', error);
    const message = error instanceof Error ? error.message : 'Internal server error in chat route';
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}
