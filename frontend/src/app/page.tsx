'use client';

import React from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { CATEGORY_LABELS, CATEGORY_ICONS } from '@/lib/constants';
import type { RequestCategory } from '@/lib/types';

const features = [
  {
    title: 'تقديم طلب مساعدة',
    description: 'قدم طلب مساعدة إنسانية بسهولة وسرعة',
    icon: '📝',
  },
  {
    title: 'تتبع الطلب',
    description: 'تابع حالة طلبك لحظة بلحظة برمز المتابعة',
    icon: '🔍',
  },
  {
    title: 'مؤسسات معتمدة',
    description: 'مؤسسات خيرية معتمدة تتكفل بتلبية الطلبات',
    icon: '🏢',
  },
  {
    title: 'إحصائيات شفافة',
    description: 'متابعة شاملة وتحليلات دقيقة للطلبات',
    icon: '📊',
  },
];

const categories = Object.entries(CATEGORY_LABELS).slice(0, 8) as [RequestCategory, string][];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero */}
      <section className="bg-gradient-to-bl from-primary-600 via-primary-700 to-primary-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-20 sm:py-28 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-6 leading-tight">
            منصة إغاثة لتنسيق
            <br />
            المساعدات الإنسانية
          </h1>
          <p className="text-lg sm:text-xl text-primary-100 mb-10 max-w-2xl mx-auto">
            نربط بين المحتاجين والمؤسسات الخيرية لتقديم المساعدة بشكل سريع ومنظم
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3 bg-white text-primary-700 rounded-lg font-semibold hover:bg-gray-100 transition-colors w-full sm:w-auto text-center"
            >
              تقديم طلب مساعدة
            </Link>
            <Link
              href="/track"
              className="px-8 py-3 border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition-colors w-full sm:w-auto text-center"
            >
              تتبع طلب سابق
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">كيف يعمل النظام؟</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, i) => (
              <div key={i} className="text-center p-6">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">أنواع المساعدات</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {categories.map(([key, label]) => (
              <div
                key={key}
                className="bg-white rounded-xl p-5 text-center shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="text-3xl mb-2">{CATEGORY_ICONS[key]}</div>
                <p className="font-medium text-gray-800">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">هل تحتاج إلى مساعدة؟</h2>
          <p className="text-primary-100 mb-8 text-lg">
            لا تتردد في تقديم طلبك. فريقنا من المؤسسات الخيرية جاهز لمساعدتك
          </p>
          <Link
            href="/register"
            className="inline-block px-8 py-3 bg-white text-primary-700 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            سجّل الآن وقدّم طلبك
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-lg font-bold text-white mb-2">KSAR - إغاثة</p>
          <p className="text-sm">منصة تنسيق المساعدات الإنسانية</p>
        </div>
      </footer>
    </div>
  );
}
