const sections = [
  ["◈", "Radar", true],
  ["◌", "Opportunities", false],
  ["◇", "Experiments", false],
  ["↗", "Impact", false],
  ["✦", "Growth DNA", false],
  ["⊙", "Permissions", false],
  ["≡", "Audit", false],
] as const;

export function Navigation() {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand">
        <span className="brand__mark" aria-hidden="true">V/</span>
        <div>
          <h2>VRUDHYA.AI</h2>
          <p>GROWTH SCIENTIST / V1.0</p>
        </div>
      </div>
      <nav className="nav">
        <p className="nav__label">LAB CONSOLE</p>
        {sections.map(([icon, label, active]) => active ? (
          <a className="nav__item nav__item--active" href="/" key={label} aria-current="page">
            <span aria-hidden="true">{icon}</span><span>{label}</span>
          </a>
        ) : (
          <span className="nav__item nav__item--disabled" key={label} aria-disabled="true">
            <span aria-hidden="true">{icon}</span><span>{label}</span>
          </span>
        ))}
      </nav>
      <div className="sidebar__footer">SETTINGS / DEVELOPMENT CONTEXT<br />MERCHANT: LUMI GIFTS</div>
    </aside>
  );
}