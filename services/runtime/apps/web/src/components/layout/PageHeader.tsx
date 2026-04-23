import type { ReactNode } from 'react';

export function PageHeader({
  eyebrow,
  title,
  description,
  badges,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  badges?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div className="page-header__body">
        {eyebrow ? <div className="page-header__eyebrow">{eyebrow}</div> : null}
        <div className="page-header__title-row">
          <div>
            <h1 className="page-header__title">{title}</h1>
            <p className="page-header__description">{description}</p>
          </div>
          {actions ? <div className="page-header__actions">{actions}</div> : null}
        </div>
        {badges ? <div className="page-header__badges">{badges}</div> : null}
      </div>
    </header>
  );
}
