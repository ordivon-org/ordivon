'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Analyze', path: '/analyze', icon: '🔍' },
  { name: 'Audits', path: '/audits', icon: '🛡️' },
  { name: 'Reports', path: '/reports', icon: '📄' },
  { name: 'History', path: '/history', icon: '⏳' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar glass" style={{
      width: '240px',
      height: '100vh',
      position: 'sticky',
      top: 0,
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem',
      borderRight: '1px solid var(--border-color)',
      backgroundColor: 'var(--sidebar-bg)'
    }}>
      <div className="logo" style={{ marginBottom: '2.5rem', fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--primary)' }}>
        PFIOS<sup>v0.1</sup>
      </div>
      
      <nav style={{ flex: 1 }}>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {navItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <li key={item.path}>
                <Link href={item.path} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  transition: 'background 0.2s',
                  backgroundColor: isActive ? 'rgba(137, 87, 229, 0.15)' : 'transparent',
                  color: isActive ? 'var(--primary-hover)' : 'var(--text-muted)',
                  fontWeight: isActive ? '600' : 'normal',
                }}>
                  <span>{item.icon}</span>
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="footer" style={{ marginTop: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        © 2026 Hermes Agentic
      </div>
    </aside>
  );
}
