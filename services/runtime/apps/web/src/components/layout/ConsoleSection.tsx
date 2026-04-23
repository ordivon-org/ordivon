import type { ReactNode } from 'react';

export function ConsoleSection({
  title,
  description,
  children,
  aside,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="console-section">
      <div className="console-section__header">
        <div>
          <h2 className="console-section__title">{title}</h2>
          {description ? <p className="console-section__description">{description}</p> : null}
        </div>
        {aside ? <div className="console-section__aside">{aside}</div> : null}
      </div>
      {children}
    </section>
  );
}
