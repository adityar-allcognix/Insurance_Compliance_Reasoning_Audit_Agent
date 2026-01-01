'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <nav className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-indigo-500 rounded flex items-center justify-center">
            <span className="text-lg font-bold">C</span>
          </div>
          <span className="text-xl font-bold tracking-tight">ComplianceAI</span>
        </Link>
        <div className="hidden md:flex space-x-8 flex-center">
          <Link href="/rules" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Rules</Link>
          <Link href="/audit" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Audit Trail</Link>
          <Link href="/metrics" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Metrics</Link>
        </div>
        <div className="flex items-center space-x-4">
          <div className="h-8 w-px bg-slate-800 mx-2 hidden md:block"></div>
          <button 
            onClick={handleLogout}
            className="text-slate-300 hover:text-white text-sm font-medium transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
