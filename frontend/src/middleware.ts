import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Route protection is handled client-side via the DashboardLayout component
// and AuthContext. This middleware handles basic redirects.
export function middleware(request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
