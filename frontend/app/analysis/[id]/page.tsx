"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api, { analysisApi } from "@/lib/api";

type Analysis = {
  id: string;
  resume_id: string;
  job_id: string;
  status: string;
  scores?: {
    ats_score?: number;
    semantic_score?: number;
    overall_score?: number;
    section_scores?: Record<string, number>;
  } | null;
  matched_skills: string[];
  missing_skills: string[];
  extra_skills: string[];
  suggestions: string[];
  improvement_tips: string[];
  summary?: string | null;
  highlights?: { type: string; text: string; start: number; end: number; score: number }[];
  resume_raw_text?: string | null;
};

export default function AnalysisPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const router = useRouter();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/${id}`);
        const analysisData = res.data;
        setAnalysis(analysisData);
        // also fetch resume to display raw_text
        if (analysisData?.resume_id) {
          const r = await api.get(`/resumes/${analysisData.resume_id}`);
          const resume = r.data;
          setAnalysis((prev) => (prev ? { ...prev, resume_raw_text: resume.raw_text } : prev));
        }
      } catch (e: any) {
        setError(e?.response?.data?.detail || "Failed to load analysis");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) return <p className="muted">Loading analysis...</p>;
  if (error) return <p className="status-warn">{error}</p>;
  if (!analysis) return <p className="muted">No analysis found.</p>;

  const renderHighlighted = () => {
    if (!analysis) return null;
    const text: string = (analysis as any).resume_raw_text || "";
    if (!text) return <p className="muted">Resume text not available.</p>;

    // Build a list of spans with styles
    const highlights = analysis.highlights || [];
    // Sort by start
    const spans = highlights.filter(h => h.start>=0).sort((a,b)=>a.start-b.start);
    const parts = [] as any[];
    let cursor = 0;
    for (const s of spans) {
      if (s.start > cursor) {
        parts.push({ text: text.slice(cursor, s.start), type: 'normal' });
      }
      parts.push({ text: text.slice(s.start, s.end), type: s.type });
      cursor = s.end;
    }
    if (cursor < text.length) parts.push({ text: text.slice(cursor), type: 'normal' });

    return (
      <div className="card">
        <pre style={{ whiteSpace: 'pre-wrap' }}>
          {parts.map((p, i) => (
            <span key={i} style={{ backgroundColor: p.type === 'matched' ? 'rgba(16,185,129,0.25)' : p.type === 'irrelevant' ? 'rgba(239,68,68,0.18)' : 'transparent' }}>
              {p.text}
            </span>
          ))}
        </pre>
      </div>
    );
  };

  return (
    <section className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Analysis</h1>
          <p className="muted">Result ID: {analysis.id}</p>
        </div>
        <div className="row">
          <button className="btn-ghost" onClick={() => router.back()}>
            Back
          </button>
        </div>
      </div>

      <article className="card stack">
        <h2>Scores</h2>
        <div className="row">
          <div className="col-4">
            <div className="badge">Overall: {analysis.scores?.overall_score ?? "—"}</div>
          </div>
          <div className="col-4">
            <div className="muted">Semantic: {analysis.scores?.semantic_score ?? "—"}</div>
          </div>
          <div className="col-4">
            <div className="muted">ATS: {analysis.scores?.ats_score ?? "—"}</div>
          </div>
        </div>
        {analysis.scores?.section_scores && Object.keys(analysis.scores.section_scores).length > 0 ? (
          <div className="list" style={{ marginTop: 10 }}>
            {Object.entries(analysis.scores.section_scores).map(([key, value]) => (
              <div key={key} className="list-item">
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <strong>{key}</strong>
                  <span className="badge">{value}</span>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </article>

      <article className="card stack">
        <h2>Matched / Missing Skills</h2>
        <div className="row">
          <div className="col-4">
            <h3>Matched</h3>
            {analysis.matched_skills.length === 0 ? <p className="muted">None</p> : null}
            <ul>
              {analysis.matched_skills.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>

          <div className="col-4">
            <h3>Missing</h3>
            {analysis.missing_skills.length === 0 ? <p className="muted">None</p> : null}
            <ul>
              {analysis.missing_skills.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>

          <div className="col-4">
            <h3>Extra</h3>
            {analysis.extra_skills.length === 0 ? <p className="muted">None</p> : null}
            <ul>
              {analysis.extra_skills.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <span className="badge">Matched: {analysis.matched_skills.length}</span>
          <span className="badge">Missing: {analysis.missing_skills.length}</span>
          <span className="badge">Extra: {analysis.extra_skills.length}</span>
        </div>
      </article>

      <article className="card stack">
        <h2>LLM Suggestions</h2>
        {analysis.suggestions.length === 0 ? <p className="muted">No suggestions available.</p> : null}
        <ul>
          {analysis.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
        {analysis.summary ? (
          <p className="muted" style={{ marginTop: 10 }}>
            Summary: {analysis.summary}
          </p>
        ) : null}
      </article>

      <article className="card stack">
        <h2>Resume (highlighted)</h2>
        {renderHighlighted()}
      </article>
    </section>
  );
}
