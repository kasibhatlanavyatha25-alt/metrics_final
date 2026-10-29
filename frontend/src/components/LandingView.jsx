import React from 'react';
import { 
  Dna, GitBranch, Activity, ShieldAlert, Sparkles, 
  ArrowRight, Search, CheckCircle2, ChevronRight, Layers, FileCode2, Cpu, TrendingUp
} from 'lucide-react';

export default function LandingView({ onStartNew, onSelectProject, existingProjects }) {
  const researchQuestions = [
    {
      q: "QUESTION 1: What is the current quality of the software?",
      a: "Quantified through comprehensive Chidamber & Kemerer (CK) metrics (LOC, WMC, CBO, RFC, LCOM, DIT, NOC) and synthesized into a normalized Software Health Score (0–100).",
      icon: Activity,
      color: "#38bdf8"
    },
    {
      q: "QUESTION 2: How has the software quality evolved across versions?",
      a: "Modeled through multi-dimensional Evolutionary Software DNA profiles tracked across historical Git milestones and tagged releases.",
      icon: Dna,
      color: "#818cf8"
    },
    {
      q: "QUESTION 3: Which metric changes/mutations are causing deterioration?",
      a: "Detected by the DNA Mutation Analyzer which isolates single and multi-gene mutations with directionality and classifies severities (Healthy, Risky, Critical).",
      icon: ShieldAlert,
      color: "#fb7185"
    },
    {
      q: "QUESTION 4: What should the developer improve first?",
      a: "Synthesized into prioritized (Critical, High, Medium, Low) explainable AI recommendations linking observed historical trends directly to actionable refactoring targets.",
      icon: Sparkles,
      color: "#34d399"
    }
  ];

  const pipelineStages = [
    { name: "Repository Validation", sub: "Git verification & language detection" },
    { name: "Version Identification", sub: "Release tags & milestones" },
    { name: "Metrics Extraction", sub: "Multi-language AST parsing" },
    { name: "Evolutionary Software DNA", sub: "5 canonical structural metrics" },
    { name: "DNA Mutation Analyzer", sub: "5D mutation vectors & severity" },
    { name: "ESDI Risk Index", sub: "Weighted 0–100 composite score" },
    { name: "Module Risk Synthesis", sub: "Source-level risk prioritization" },
    { name: "AI Recommendation Engine", sub: "Evidence-backed action cards" },
    { name: "Future Quality Prediction", sub: "Statistical trend extrapolation" },
  ];

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Header */}
      <div className="relative overflow-hidden glass-panel p-8 md:p-12 border-indigo-500/20 bg-gradient-to-br from-indigo-950/40 via-slate-900/60 to-slate-950/80">
        <div className="max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
            <Dna className="w-4 h-4 text-indigo-400 animate-spin" style={{ animationDuration: '8s' }} />
            Academic Research System
          </div>
          
          <h1 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
            AI-Based Software Metrics Recommendation System using <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400">Evolutionary Software DNA</span>
          </h1>
          
          <p className="text-slate-300 text-base md:text-lg leading-relaxed max-w-3xl">
            A full-stack empirical research platform performing real AST software metrics extraction, Git history evolution modeling, DNA mutation classification, and explainable refactoring recommendation generation for multi-language Git repositories (Java, Python, TypeScript, JavaScript).
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <button 
              onClick={onStartNew}
              className="btn-primary px-6 py-3 text-base shadow-lg shadow-indigo-500/25 cursor-pointer"
            >
              <Search className="w-5 h-5" />
              Analyze Git Repository
            </button>
            {existingProjects && existingProjects.length > 0 && (
              <button 
                onClick={() => onSelectProject(existingProjects[0].id)}
                className="btn-secondary px-6 py-3 text-base cursor-pointer"
              >
                <Layers className="w-5 h-5 text-indigo-400" />
                View Latest Analysis ({existingProjects[0].name})
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 4 Core Research Questions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Core Research Questions Addressed
          </h2>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-mono">Empirical Framework</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {researchQuestions.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="glass-panel p-6 space-y-3 relative group hover:border-slate-600 transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60" style={{ color: item.color }}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-sm md:text-base text-slate-100">{item.q}</h3>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed pl-12">
                  {item.a}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Architectural Flow */}
      <div className="glass-panel p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white">System Architecture & Analytical Flow</h2>
            <p className="text-xs text-slate-400 mt-1">Sequential 9-tier data pipeline executing without fabricated or synthetic artifacts</p>
          </div>
          <span className="badge badge-moderate">Real Git & AST Pipeline</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelineStages.map((st, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 font-mono text-xs font-bold shrink-0">
                {i + 1}
              </span>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">{st.name}</h4>
                <p className="text-xs text-slate-400 mt-0.5">{st.sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Existing Analyzed Projects */}
      {existingProjects && existingProjects.length > 0 && (
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Recently Analyzed Repositories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {existingProjects.map((p) => (
              <div 
                key={p.id} 
                onClick={() => onSelectProject(p.id)}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-850 cursor-pointer transition-all space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-base truncate">{p.name}</span>
                  <span className={`badge badge-${(p.status || 'healthy').toLowerCase()}`}>
                    {p.status || 'ANALYZED'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-slate-400 font-mono">
                  <div>
                    <span className="block text-slate-500">Versions</span>
                    <span className="text-slate-200 font-semibold">{p.total_versions}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500">Classes</span>
                    <span className="text-slate-200 font-semibold">{p.total_classes}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500">Health</span>
                    <span className="text-emerald-400 font-semibold">{p.health_score || 0}/100</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-indigo-400 pt-2 border-t border-slate-800/60 font-medium">
                  <span>Open Full Dashboard</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
