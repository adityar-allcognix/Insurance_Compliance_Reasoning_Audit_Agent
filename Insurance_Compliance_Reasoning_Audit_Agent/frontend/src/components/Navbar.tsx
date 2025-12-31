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
    <nav className="bg-slate-900 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/dashboard" className="text-xl font-bold">Compliance Audit</Link>
        <div className="space-x-6 flex items-center">
          <Link href="/rules" className="hover:text-slate-300">Rules</Link>
          <Link href="/audit" className="hover:text-slate-300">Audit Trail</Link>
          <Link href="/metrics" className="hover:text-slate-300">Metrics</Link>
          <button 
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
