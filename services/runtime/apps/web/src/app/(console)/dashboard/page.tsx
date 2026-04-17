export default function DashboardPage() {
  return (
    <main style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 16 }}>PFIOS Dashboard</h1>

      <section style={{ display: "grid", gap: 16 }}>
        <div style={{ padding: 16, border: "1px solid #2d3748", borderRadius: 12 }}>
          <h2>System Health</h2>
          <p>Step 1 skeleton initialized.</p>
        </div>

        <div style={{ padding: 16, border: "1px solid #2d3748", borderRadius: 12 }}>
          <h2>Analyze</h2>
          <p>Analyze / Governance / Audit chain will be connected in later steps.</p>
        </div>

        <div style={{ padding: 16, border: "1px solid #2d3748", borderRadius: 12 }}>
          <h2>Recommendations</h2>
          <p>Recommendation lifecycle starts in Step 10.</p>
        </div>

        <div style={{ padding: 16, border: "1px solid #2d3748", borderRadius: 12 }}>
          <h2>Reviews</h2>
          <p>Review loop starts in Step 10.</p>
        </div>
      </section>
    </main>
  );
}
