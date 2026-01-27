'use client';

export function CardSkeleton() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
      <div className="h-6 bg-slate-800 rounded w-1/3 mb-4"></div>
      <div className="space-y-3">
        <div className="h-4 bg-slate-800 rounded w-full"></div>
        <div className="h-4 bg-slate-800 rounded w-5/6"></div>
        <div className="h-4 bg-slate-800 rounded w-4/6"></div>
      </div>
    </div>
  );
}

export function MetricsSkeleton() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
      <div className="h-6 bg-slate-800 rounded w-1/3 mb-6"></div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-slate-800 rounded-lg p-4">
            <div className="h-4 bg-slate-700 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-slate-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
      <div className="h-[400px] bg-slate-800 rounded"></div>
    </div>
  );
}

export function TimelineSkeleton() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
      <div className="h-6 bg-slate-800 rounded w-1/4 mb-6"></div>
      <div className="space-y-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-4">
            <div className="w-4 h-4 bg-slate-800 rounded-full"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-800 rounded w-1/4"></div>
              <div className="h-5 bg-slate-800 rounded w-3/4"></div>
              <div className="h-4 bg-slate-800 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function IncidentCardSkeleton() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex gap-3 mb-3">
            <div className="h-6 bg-slate-800 rounded w-12"></div>
            <div className="h-4 bg-slate-800 rounded w-32"></div>
          </div>
          <div className="h-6 bg-slate-800 rounded w-3/4 mb-3"></div>
        </div>
        <div className="h-6 w-6 bg-slate-800 rounded"></div>
      </div>
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="space-y-2">
            <div className="h-3 bg-slate-800 rounded w-16"></div>
            <div className="h-4 bg-slate-800 rounded w-12"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
