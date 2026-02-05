'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const getDashboardLink = () => {
    if (!user) return '/login';
    switch (user.role) {
      case 'admin':
        return '/admin';
      case 'organization':
        return '/org/requests';
      case 'citizen':
        return '/citizen';
      default:
        return '/';
    }
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl font-bold text-primary-600">KSAR</span>
              <span className="text-sm text-gray-500">| إغاثة</span>
            </Link>

            <div className="hidden md:flex items-center gap-4">
              <Link href="/" className="text-sm text-gray-600 hover:text-primary-600 transition-colors">
                الرئيسية
              </Link>
              <Link href="/track" className="text-sm text-gray-600 hover:text-primary-600 transition-colors">
                تتبع طلب
              </Link>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated && user ? (
              <>
                <Link
                  href={getDashboardLink()}
                  className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
                >
                  لوحة التحكم
                </Link>
                <span className="text-sm text-gray-400">|</span>
                <span className="text-sm text-gray-600">{user.full_name}</span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-red-600 hover:text-red-700 transition-colors"
                >
                  خروج
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm px-4 py-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                >
                  دخول
                </Link>
                <Link
                  href="/register"
                  className="text-sm px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  تسجيل
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="text-gray-600 hover:text-gray-900"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {menuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white">
          <div className="px-4 py-3 space-y-2">
            <Link href="/" className="block text-sm text-gray-600 py-2" onClick={() => setMenuOpen(false)}>
              الرئيسية
            </Link>
            <Link href="/track" className="block text-sm text-gray-600 py-2" onClick={() => setMenuOpen(false)}>
              تتبع طلب
            </Link>
            {isAuthenticated && user ? (
              <>
                <Link href={getDashboardLink()} className="block text-sm text-gray-600 py-2" onClick={() => setMenuOpen(false)}>
                  لوحة التحكم
                </Link>
                <button onClick={handleLogout} className="block text-sm text-red-600 py-2">
                  خروج
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="block text-sm text-primary-600 py-2" onClick={() => setMenuOpen(false)}>
                  دخول
                </Link>
                <Link href="/register" className="block text-sm text-primary-600 py-2" onClick={() => setMenuOpen(false)}>
                  تسجيل
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
