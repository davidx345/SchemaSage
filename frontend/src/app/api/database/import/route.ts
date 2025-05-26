import { NextResponse } from 'next/server';
import type { DatabaseConfig } from '@/lib/types';
import { API_BASE_URL } from '@/lib/config';

export async function POST(req: Request) {
  try {
    const config: DatabaseConfig = await req.json();
    
    const response = await fetch( `${API_BASE_URL}/api/database/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || 'Failed to import from database',
          details: error.details
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Database import error:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}