'use client';

import React, { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import StatsCard from '@/components/ui/StatsCard';
import { Card, CardTitle } from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { adminApi } from '@/lib/api';
import { CATEGORY_LABELS, REQUEST_STATUS_LABELS } from '@/lib/constants';
import type { RequestCategory, RequestStatus } from '@/lib/types';

interface OverviewData {
  total_requests: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  urgent_count: number;
  avg_completion_hours: number | null;
  active_organizations: number;
}

interface DailyItem {
  date: string;
  count: number;
}

interface RegionalItem {
  region: string;
  total: number;
  new: number;
  completed: number;
}

interface OrgStatItem {
  id: string;
  name: string;
  total_assignments: number;
  completed: number;
}

export default function AdminDashboard() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [daily, setDaily] = useState<DailyItem[]>([]);
  const [regions, setRegions] = useState<RegionalItem[]>([]);
  const [orgStats, setOrgStats] = useState<OrgStatItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overviewRes, dailyRes, regionsRes, orgRes] = await Promise.all([
        adminApi.getOverviewStats(),
        adminApi.getDailyStats(14),
        adminApi.getRegionalStats(),
        adminApi.getOrgStats(),
      ]);
      setOverview(overviewRes.data);
      setDaily(dailyRes.data);
      setRegions(regionsRes.data);
      setOrgStats(orgRes.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12"><Spinner /></div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">لوحة الإحصائيات</h1>
        <p className="text-gray-500 mt-1">نظرة عامة على نظام المساعدات</p>
      </div>

      {overview && (
        <>
          {/* Top Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard
              title="إجمالي الطلبات"
              value={overview.total_requests}
              color="text-primary-600"
            />
            <StatsCard
              title="طلبات مستعجلة"
              value={overview.urgent_count}
              color="text-red-600"
            />
            <StatsCard
              title="المؤسسات النشطة"
              value={overview.active_organizations}
              color="text-green-600"
            />
            <StatsCard
              title="متوسط وقت الإنجاز"
              value={overview.avg_completion_hours ? `${overview.avg_completion_hours}h` : '-'}
              subtitle="بالساعات"
              color="text-orange-600"
            />
          </div>

          {/* Status breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <Card>
              <CardTitle>الطلبات حسب الحالة</CardTitle>
              <div className="mt-4 space-y-3">
                {Object.entries(overview.by_status).map(([status, count]) => {
                  const percentage = overview.total_requests > 0
                    ? Math.round((count / overview.total_requests) * 100)
                    : 0;
                  return (
                    <div key={status}>
                      <div className="flex justify-between text-sm mb-1">
                        <span>{REQUEST_STATUS_LABELS[status as RequestStatus] || status}</span>
                        <span className="text-gray-500">{count} ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card>
              <CardTitle>الطلبات حسب التصنيف</CardTitle>
              <div className="mt-4 space-y-3">
                {Object.entries(overview.by_category)
                  .sort((a, b) => b[1] - a[1])
                  .map(([category, count]) => {
                    const percentage = overview.total_requests > 0
                      ? Math.round((count / overview.total_requests) * 100)
                      : 0;
                    return (
                      <div key={category}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{CATEGORY_LABELS[category as RequestCategory] || category}</span>
                          <span className="text-gray-500">{count} ({percentage}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div
                            className="bg-accent-500 h-2 rounded-full transition-all"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </Card>
          </div>
        </>
      )}

      {/* Daily chart (simple bar chart) */}
      {daily.length > 0 && (
        <Card className="mb-8">
          <CardTitle>الطلبات اليومية (آخر 14 يوم)</CardTitle>
          <div className="mt-4 flex items-end gap-1 h-40">
            {daily.map((d) => {
              const maxCount = Math.max(...daily.map((x) => x.count), 1);
              const height = (d.count / maxCount) * 100;
              return (
                <div
                  key={d.date}
                  className="flex-1 flex flex-col items-center"
                  title={`${d.date}: ${d.count} طلب`}
                >
                  <span className="text-xs text-gray-400 mb-1">{d.count}</span>
                  <div
                    className="w-full bg-primary-400 rounded-t min-h-[4px]"
                    style={{ height: `${Math.max(height, 3)}%` }}
                  />
                  <span className="text-[10px] text-gray-400 mt-1 rotate-[-45deg]">
                    {d.date.slice(5)}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regional stats */}
        {regions.length > 0 && (
          <Card>
            <CardTitle>الطلبات حسب المنطقة</CardTitle>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b">
                    <th className="text-right pb-2">المنطقة</th>
                    <th className="text-center pb-2">الإجمالي</th>
                    <th className="text-center pb-2">جديد</th>
                    <th className="text-center pb-2">مكتمل</th>
                  </tr>
                </thead>
                <tbody>
                  {regions.map((r) => (
                    <tr key={r.region} className="border-b border-gray-50">
                      <td className="py-2">{r.region}</td>
                      <td className="text-center py-2 font-medium">{r.total}</td>
                      <td className="text-center py-2 text-blue-600">{r.new}</td>
                      <td className="text-center py-2 text-green-600">{r.completed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Organization stats */}
        {orgStats.length > 0 && (
          <Card>
            <CardTitle>أداء المؤسسات</CardTitle>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b">
                    <th className="text-right pb-2">المؤسسة</th>
                    <th className="text-center pb-2">التكفلات</th>
                    <th className="text-center pb-2">مكتمل</th>
                    <th className="text-center pb-2">النسبة</th>
                  </tr>
                </thead>
                <tbody>
                  {orgStats.map((o) => (
                    <tr key={o.id} className="border-b border-gray-50">
                      <td className="py-2">{o.name}</td>
                      <td className="text-center py-2">{o.total_assignments}</td>
                      <td className="text-center py-2 text-green-600">{o.completed}</td>
                      <td className="text-center py-2">
                        {o.total_assignments > 0
                          ? `${Math.round((o.completed / o.total_assignments) * 100)}%`
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
