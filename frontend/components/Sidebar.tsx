"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Zap, BookOpen, Activity } from "lucide-react";
import clsx from "clsx";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/events", label: "Live Events", icon: Activity },
  { href: "/simulator", label: "Simulator", icon: Zap },
  { href: "/attribution", label: "Attribution Ledger", icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-gray-900 border-r border-gray-800 flex flex-col z-50">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">R</div>
          <div>
            <p className="font-semibold text-white text-sm">RevEngine AI</p>
            <p className="text-xs text-gray-400">Revenue Recovery</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname === href
                ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                : "text-gray-400 hover:bg-gray-800 hover:text-white"
            )}>
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>

      {/* Razorpay badge */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400">Powered by</p>
          <p className="text-sm font-semibold text-blue-400 mt-0.5">Razorpay Buildathon</p>
          <p className="text-xs text-gray-500 mt-0.5">2025</p>
        </div>
      </div>
    </aside>
  );
}
