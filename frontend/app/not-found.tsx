import Link from 'next/link';
import { Home, AlertCircle, ArrowLeft, Brain } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-6">
      <div className="text-center max-w-lg">
        {/* 404 Display */}
        <div className="relative mb-8">
          <h1 className="text-[180px] font-bold text-slate-800 leading-none">404</h1>
          <div className="absolute inset-0 flex items-center justify-center">
            <AlertCircle className="h-24 w-24 text-blue-500/50" />
          </div>
        </div>

        {/* Message */}
        <h2 className="text-3xl font-bold text-white mb-4">Page Not Found</h2>
        <p className="text-slate-400 mb-8">
          The page you're looking for doesn't exist or has been moved.
          Let's get you back on track.
        </p>

        {/* Navigation Options */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:scale-105 transition-transform"
          >
            <Home className="h-5 w-5" />
            Back to Home
          </Link>
          <Link
            href="/incidents"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold transition-colors border border-slate-700"
          >
            <ArrowLeft className="h-5 w-5" />
            View Incidents
          </Link>
        </div>

        {/* Additional Links */}
        <div className="mt-12 pt-8 border-t border-slate-800">
          <p className="text-slate-500 text-sm mb-4">Quick Links</p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/dashboard" className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1">
              <Brain className="h-4 w-4" />
              Predictive Dashboard
            </Link>
            <span className="text-slate-700">|</span>
            <Link href="/incidents" className="text-blue-400 hover:text-blue-300 text-sm">
              Incidents
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
