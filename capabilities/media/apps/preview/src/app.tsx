import {RuntimeFlow, runtimeStages, type RuntimeStage} from '@ordivon/visuals';
import {useState} from 'react';
import production from '../../../productions/runtime-introduction/production.json';

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
    </main>
  );
}
