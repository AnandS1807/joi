"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { analysisApi, jobsApi, resumesApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

type ResumeItem = {
  id: string;
  filename: string;
  status: string;
  created_at?: string;
};

type JobItem = {
  id: string;
  title?: string;
  company?: string;
  status: string;
  created_at?: string;
};

type AnalysisItem = {
  id: string;
  resume_id: string;
  job_id: string;
  status: string;
  scores?: {
    overall_score?: number;
  } | null;
  created_at?: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const { hydrate, logout, user } = useAuthStore();

  const [ready, setReady] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedJob, setSelectedJob] = useState("");

  const username = useMemo(() => {
    if (user?.full_name) return user.full_name;
    if (user?.email) return user.email;
    return "there";
  }, [user]);

  async function loadAll() {
    setLoadingData(true);
    setError("");
    try {
      const [resumeRes, jobsRes, analysisRes] = await Promise.all([
        resumesApi.list(),
        jobsApi.list(),
        analysisApi.list(),
      ]);

      setResumes(resumeRes.data?.resumes || []);
      setJobs(jobsRes.data || []);
      setAnalyses(analysisRes.data || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load dashboard data");
    } finally {
      setLoadingData(false);
    }
  }

  useEffect(() => {
    hydrate();

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    setReady(true);
  }, [hydrate, router]);

  useEffect(() => {
    if (!ready) return;
    loadAll();
  }, [ready]);

  async function onUploadResume(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please choose a PDF file first");
      return;
    }

    setError("");
    setMessage("");
    try {
      await resumesApi.upload(file);
      setFile(null);
      setMessage("Resume uploaded successfully");
      await loadAll();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to upload resume");
    }
  }

  async function onCreateJob(e: React.FormEvent) {
    e.preventDefault();
    if (!jobFile) {
      setError("Please choose a JD file first");
      return;
    }

    setError("");
    setMessage("");
    try {
      await jobsApi.upload(jobFile);
      setJobFile(null);
      setMessage("Job description uploaded");
      await loadAll();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to upload job file");
    }
  }

  async function onRunAnalysis(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedResume || !selectedJob) {
      setError("Select both a resume and a job to run analysis");
      return;
    }

    setError("");
    setMessage("");
    try {
      await analysisApi.run({ resume_id: selectedResume, job_id: selectedJob });
      setMessage("Analysis job queued");
      await loadAll();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to run analysis");
    }
  }

  if (!ready) return <p className="muted">Checking session...</p>;

  return (
    <section className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Workspace</h1>
          <p className="muted">Hello {username}. Upload resumes, add job descriptions, and run analysis.</p>
        </div>
        <div className="row">
          <span className="badge">Backend linked</span>
          <button className="btn-ghost" onClick={logout} type="button">
            Logout
          </button>
        </div>
      </div>

      {loadingData ? <p className="muted">Refreshing data...</p> : null}
      {message ? <p className="status-ok">{message}</p> : null}
      {error ? <p className="status-warn">{error}</p> : null}

      <div className="grid">
        <article className="card col-6 stack">
          <h2>Resume Library</h2>
          <form className="stack" onSubmit={onUploadResume}>
            <label>
              Upload PDF
              <input
                accept=".pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                type="file"
              />
            </label>
            <button className="btn-secondary" type="submit">
              Upload Resume
            </button>
          </form>

          <div className="list">
            {resumes.length === 0 ? <p className="muted">No resumes yet.</p> : null}
            {resumes.map((r) => (
              <div className="list-item" key={r.id}>
                <strong>{r.filename}</strong>
                <div className="row" style={{ justifyContent: "space-between", marginTop: 6 }}>
                  <span className="muted">{r.id}</span>
                  <span className="badge">{r.status}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="card col-6 stack">
          <h2>Job Descriptions</h2>
          <form className="stack" onSubmit={onCreateJob}>
            <label>
              Upload JD File (PDF or TXT)
              <input
                accept=".pdf,.txt"
                onChange={(e) => setJobFile(e.target.files?.[0] || null)}
                type="file"
              />
            </label>

            <button className="btn-primary" type="submit">
              Upload Job Description
            </button>
          </form>

          <div className="list">
            {jobs.length === 0 ? <p className="muted">No jobs yet.</p> : null}
            {jobs.map((j) => (
              <div className="list-item" key={j.id}>
                <strong>{j.title || "Untitled Job"}</strong>
                <div className="row" style={{ justifyContent: "space-between", marginTop: 6 }}>
                  <span className="muted">{j.company || "Unknown company"}</span>
                  <span className="badge">{j.status}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="card col-12 stack">
          <h2>Analysis Runner</h2>
          <p className="muted">Pick one resume and one job to create an analysis request.</p>
          <form className="row" onSubmit={onRunAnalysis}>
            <select onChange={(e) => setSelectedResume(e.target.value)} value={selectedResume}>
              <option value="">Select resume</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename}
                </option>
              ))}
            </select>

            <select onChange={(e) => setSelectedJob(e.target.value)} value={selectedJob}>
              <option value="">Select job</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title || j.id}
                </option>
              ))}
            </select>

            <button className="btn-primary" type="submit">
              Run Analysis
            </button>
          </form>

          <div className="list">
            {analyses.length === 0 ? <p className="muted">No analyses yet.</p> : null}
            {analyses.map((a) => (
              <div className="list-item" key={a.id}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <strong>{a.id}</strong>
                  <span className="badge">
                    {a.status}
                    {a.scores?.overall_score !== undefined ? ` • ${a.scores.overall_score}` : ""}
                  </span>
                </div>
                <div className="muted" style={{ marginTop: 6 }}>
                  Resume: {a.resume_id} | Job: {a.job_id}
                </div>
                <div className="row" style={{ marginTop: 10 }}>
                  <Link className="btn-ghost" href={`/analysis/${a.id}`}>
                    View Analysis
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
