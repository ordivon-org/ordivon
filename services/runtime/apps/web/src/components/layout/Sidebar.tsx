'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Dashboard', path: '/', icon: 'D' },
  { name: 'Analyze', path: '/analyze', icon: 'A' },
  { name: 'Reviews', path: '/reviews', icon: 'R' },
  { name: 'Audits', path: '/audits', icon: 'Au' },
  { name: 'Reports', path: '/reports', icon: 'Re' },
  { name: 'History', path: '/history', icon: 'H' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar glass">
      <div className="sidebar__logo">
        PFIOS<sup>v0.1</sup>
      </div>

      <nav className="sidebar__nav">
        <ul className="sidebar__nav-list">
          {navItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={`sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
                >
                  <span className="sidebar__icon">{item.icon}</span>
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sidebar__footer">
        2026 AegisOS Console
      </div>
    </aside>
  );
}
