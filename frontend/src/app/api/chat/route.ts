import { NextResponse } from 'next/server';
import { API_BASE_URL } from '@/lib/config';
// Removed unused ChatMessage interface

export async function POST(req: Request) {
  try {
    const { messages, context } = await req.json();
    
    // Extract schema data from context to match backend's expected format
    const schema_data = context?.schema;
    
    if (!schema_data) {
      return NextResponse.json(
        { error: 'Schema data is required for chat' },
        { status: 400 }
      );
    }

    // Restructure request to match backend's expected format
    const response = await fetch(`${API_BASE_URL}/api/schema/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        schema_data: schema_data,
        messages: messages.map((msg: {role: string; content: string}) => ({
          role: msg.role,
          content: msg.content
        }))
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || error.detail || 'Chat service error' },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Chat error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
