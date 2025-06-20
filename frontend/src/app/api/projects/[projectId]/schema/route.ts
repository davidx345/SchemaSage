import { NextRequest, NextResponse } from 'next/server';
import type { SchemaResponse } from '@/lib/types';
import { API_BASE_URL } from '@/lib/config';

export async function GET(request: NextRequest, context: { params: Promise<{ projectId: string }> }) {
  try {
    const { projectId } = await context.params;
    
    const response = await fetch(`${API_BASE_URL}/api/database/projects/${projectId}/schema`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || `Failed to retrieve schema for project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error(`Get schema for project error:`, error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const { projectId } = await params;
    const schema: SchemaResponse = await req.json();
    
    const response = await fetch(`${API_BASE_URL}/api/database/projects/${projectId}/schema`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(schema),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || `Failed to save schema for project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error(`Save schema for project error:`, error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}