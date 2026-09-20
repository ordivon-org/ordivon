import {RuntimeFlow, runtimeStages, type RuntimeStage} from '@ordivon/visuals';
import {useState} from 'react';
import production from '../../../productions/runtime-introduction/production.json';
import receipt from '../../../productions/runtime-introduction/evidence/runtime-demo.receipt.json';

function compact(value: string, head = 14, tail = 8): string {
  if (value.length <= head + tail + 1) return value;
  return `${value.slice(0, head)}…${value.slice(-tail)}`;
}

export function App() {
  const [activeStage, setActiveStage] = useState<RuntimeStage>('job');

  return (
    <main>
      <header className="studio-header">
        <p>Ordivon Studio / Source Preview</p>
        <span>{production.status}</span>
      </header>

      <section className="hero">
        <p className="eyebrow">Production 001</p>
        <h1>{production.title}</h1>
        <p>{production.intent}</p>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Shared visual primitive</p>
            <h2>Runtime execution flow</h2>
          </div>
          <div className="stage-controls" aria-label="Select active Runtime stage">
            {runtimeStages.map((stage) => (
              <button key={stage.id} className={activeStage === stage.id ? 'active' : ''} onClick={() => setActiveStage(stage.id)}>
                {stage.id}
              </button>
            ))}
          </div>
        </div>
        <RuntimeFlow activeStage={activeStage} />
      </section>

      <section className="facts">
        <article>
          <span>Source revision</span>
          <strong>{production.sourceBindings[0]?.revision.slice(0, 12)}</strong>
        </article>
        <article>
          <span>Working canvas</span>
          <strong>{production.workingProfile.canvas.width} × {production.workingProfile.canvas.height}</strong>
        </article>
        <article>
          <span>Frame rate</span>
          <strong>{production.workingProfile.frameRate.numerator}/{production.workingProfile.frameRate.denominator}</strong>
        </article>
        <article>
          <span>Audio</span>
          <strong>{production.workingProfile.audio.sampleRate / 1000} kHz / {production.workingProfile.audio.sourceBitDepth}-bit</strong>
        </article>
      </section>

      <section className="receipt-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Validated live receipt</p>
            <h2>Recovery proof, not a mockup</h2>
          </div>
          <code>{compact(receipt.toolCatalogDigest)}</code>
        </div>
        <div className="receipt-grid">
          <article>
            <span>Exact replay</span>
            <strong>{receipt.execution.sameJobAfterReplay ? 'same Job' : 'failed'}</strong>
            <code>{compact(receipt.execution.jobId, 20, 10)}</code>
          </article>
          <article>
            <span>Recorded Attempt</span>
            <strong>{receipt.execution.status}</strong>
            <code>{compact(receipt.execution.attemptId, 20, 10)}</code>
          </article>
          <article>
            <span>Terminal evidence</span>
            <strong>{receipt.execution.elapsedMs / 1000}s</strong>
            <code>{compact(receipt.evidence.digest)}</code>
          </article>
          <article>
            <span>Compare-and-close</span>
            <strong>{receipt.close.exactStateMatched ? 'exact match' : 'blocked'}</strong>
            <code>{compact(receipt.close.sourceStateDigest)}</code>
          </article>
        </div>
      </section>
    </main>
  );
}
