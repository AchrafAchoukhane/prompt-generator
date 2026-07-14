"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

const categories = [
  "General",
  "Image Generation",
  "Code Generation",
  "Writing",
  "Research",
  "Data Analysis",
  "Cybersecurity",
  "Learning",
] as const;

type TaskType = (typeof categories)[number];

type Optimization = {
  id: string;
  original_prompt: string;
  optimized_prompt: string;
  task_type: TaskType;
  original_score: number;
  optimized_score: number;
  weaknesses: string[];
  improvements: string[];
  missing_information: string[];
  score_breakdown: Record<string, number>;
  provider: string;
  model: string | null;
  created_at: string;
};

type HistoryResponse = {
  items: Optimization[];
  total: number;
};

const examples: Record<string, string> = {
  Image: "Crée une image pour une campagne de café artisanal sur Instagram",
  Code: "Développe une API pour gérer les réservations d'un restaurant",
  Writing: "Rédige un email pour annoncer notre nouvelle offre aux clients",
  Learning: "Explique-moi les probabilités conditionnelles simplement",
};

const categoryMarks: Record<TaskType, string> = {
  General: "GE",
  "Image Generation": "IM",
  "Code Generation": "CO",
  Writing: "WR",
  Research: "RE",
  "Data Analysis": "DA",
  Cybersecurity: "CY",
  Learning: "LE",
};

function ScoreDial({ score, label }: { score: number; label: string }) {
  return (
    <div className="score-block">
      <div className="score-dial" style={{ "--score": `${score * 3.6}deg` } as React.CSSProperties}>
        <div className="score-dial__inner">
          <strong>{score}</strong>
          <span>/100</span>
        </div>
      </div>
      <span className="score-label">{label}</span>
    </div>
  );
}

function ResultPanel({ result }: { result: Optimization }) {
  const [copied, setCopied] = useState(false);

  async function copyOptimizedPrompt() {
    await navigator.clipboard.writeText(result.optimized_prompt);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <section className="result-shell" aria-live="polite">
      <div className="result-head">
        <div>
          <span className="eyebrow">Analyse terminée</span>
          <div className="task-pill">
            <span>{categoryMarks[result.task_type]}</span>
            {result.task_type}
          </div>
        </div>
        <div className="score-comparison" aria-label={`Score amélioré de ${result.original_score} à ${result.optimized_score}`}>
          <ScoreDial score={result.original_score} label="Avant" />
          <span className="score-arrow">→</span>
          <ScoreDial score={result.optimized_score} label="Après" />
        </div>
      </div>

      <div className="prompt-comparison">
        <article className="prompt-card prompt-card--original">
          <div className="card-kicker"><span>01</span> Prompt original</div>
          <p>{result.original_prompt}</p>
        </article>
        <article className="prompt-card prompt-card--optimized">
          <div className="card-kicker">
            <span>02</span> Prompt optimisé
            <button className="copy-button" type="button" onClick={copyOptimizedPrompt}>
              {copied ? "Copié !" : "Copier"}
            </button>
          </div>
          <pre>{result.optimized_prompt}</pre>
        </article>
      </div>

      <div className="insight-grid">
        <article className="insight-card insight-card--positive">
          <div className="insight-title"><span>+</span> Améliorations</div>
          <ul>
            {result.improvements.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>
        <article className="insight-card insight-card--warning">
          <div className="insight-title"><span>?</span> Informations manquantes</div>
          {result.missing_information.length ? (
            <ul>{result.missing_information.map((item) => <li key={item}>{item}</li>)}</ul>
          ) : (
            <p className="empty-note">Le brief contient les informations essentielles.</p>
          )}
        </article>
      </div>
      <p className="provider-note">
        Optimisation par {result.provider === "openai" ? result.model ?? "OpenAI" : "le moteur local"}
      </p>
    </section>
  );
}

function EmptyResult() {
  return (
    <section className="empty-result">
      <div className="empty-orbit" aria-hidden="true"><span>PG</span></div>
      <span className="eyebrow">Votre atelier</span>
      <h2>Un prompt solide est une petite architecture.</h2>
      <p>Nous évaluons sept dimensions utiles, puis reconstruisons uniquement ce qui manque à votre demande.</p>
      <div className="rubric-list">
        {["Objectif", "Contexte", "Public", "Format", "Contraintes", "Précision", "Réussite"].map((item, index) => (
          <div key={item}><span>{String(index + 1).padStart(2, "0")}</span>{item}</div>
        ))}
      </div>
    </section>
  );
}

export function PromptWorkspace() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<Optimization | null>(null);
  const [history, setHistory] = useState<Optimization[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const characterCount = useMemo(() => prompt.length, [prompt]);

  const loadHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/optimizations?limit=8`, { cache: "no-store" });
      if (!response.ok) throw new Error("Historique indisponible");
      const data = (await response.json()) as HistoryResponse;
      setHistory(data.items);
      setHistoryTotal(data.total);
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  async function submitPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (prompt.trim().length < 3) {
      setError("Saisissez une demande d'au moins trois caractères.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/optimizations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      if (!response.ok) {
        const details = await response.json().catch(() => null);
        throw new Error(details?.detail?.[0]?.msg ?? "L'optimisation a échoué.");
      }
      const optimization = (await response.json()) as Optimization;
      setResult(optimization);
      setApiOnline(true);
      await loadHistory();
    } catch (caught) {
      setApiOnline(false);
      setError(caught instanceof Error ? caught.message : "Impossible de joindre l'API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Prompt Generator — accueil">
          <span className="brand-mark">P<span>G</span></span>
          <span>Prompt Generator<small>Prompt clarity studio</small></span>
        </a>
        <a className="history-link" href="#history">Historique <span>{historyTotal}</span></a>
      </header>

      <div className="category-ribbon" aria-label="Catégories prises en charge">
        <div className="category-track">
          {categories.map((category) => <span key={category}>{categoryMarks[category]} · {category}</span>)}
        </div>
      </div>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="status-line">
            <span className={`status-dot ${apiOnline === false ? "status-dot--down" : ""}`} />
            {apiOnline === false ? "API hors ligne" : apiOnline ? "Moteur prêt" : "Connexion au moteur…"}
          </div>
          <h1>De l’idée brute<br />au <em>prompt juste.</em></h1>
          <p className="hero-lede">
            Décrivez votre besoin naturellement. Le moteur détecte la tâche, révèle les zones floues et compose un prompt réellement adapté.
          </p>

          <form className="prompt-form" onSubmit={submitPrompt}>
            <div className="textarea-head">
              <label htmlFor="prompt">Votre demande</label>
              <span>{characterCount.toLocaleString("fr-FR")} / 12 000</span>
            </div>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              maxLength={12_000}
              placeholder="Ex. Crée une campagne Instagram pour le lancement de notre café de spécialité…"
              rows={7}
              disabled={loading}
            />
            <div className="form-footer">
              <span>Détection automatique du type de tâche</span>
              <button className="optimize-button" type="submit" disabled={loading || prompt.trim().length < 3}>
                {loading ? <><i className="spinner" /> Analyse en cours</> : <>Optimiser <b>↗</b></>}
              </button>
            </div>
          </form>
          {error && <div className="error-banner" role="alert">{error}</div>}

          <div className="examples">
            <span>Essayez un exemple</span>
            <div>
              {Object.entries(examples).map(([label, value]) => (
                <button key={label} type="button" onClick={() => setPrompt(value)}>{label}</button>
              ))}
            </div>
          </div>
        </div>

        <div className="hero-result">
          {result ? <ResultPanel result={result} /> : <EmptyResult />}
        </div>
      </section>

      {result && (
        <section className="weakness-strip">
          <span className="eyebrow">Diagnostic original</span>
          <div>
            {result.weaknesses.map((weakness, index) => (
              <article key={weakness}><span>{String(index + 1).padStart(2, "0")}</span><p>{weakness}</p></article>
            ))}
          </div>
        </section>
      )}

      <section className="history-section" id="history">
        <div className="section-heading">
          <div><span className="eyebrow">Mémoire de travail</span><h2>Optimisations récentes</h2></div>
          <p>{historyTotal ? `${historyTotal} prompt${historyTotal > 1 ? "s" : ""} conservé${historyTotal > 1 ? "s" : ""}` : "Votre historique apparaîtra ici"}</p>
        </div>
        {history.length ? (
          <div className="history-grid">
            {history.map((item) => (
              <button className="history-card" type="button" key={item.id} onClick={() => { setResult(item); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
                <span className="history-category"><i>{categoryMarks[item.task_type]}</i>{item.task_type}</span>
                <strong>{item.original_prompt}</strong>
                <span className="history-meta">
                  <time>{new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(item.created_at))}</time>
                  <b>{item.original_score} → {item.optimized_score}</b>
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="history-empty">Lancez votre première optimisation pour créer l’historique.</div>
        )}
      </section>

      <footer>
        <div className="brand brand--footer"><span className="brand-mark">P<span>G</span></span><span>Prompt Generator</span></div>
        <p>Conçu pour demander mieux, pas pour demander plus.</p>
        <span>MVP · 2026</span>
      </footer>
    </main>
  );
}
