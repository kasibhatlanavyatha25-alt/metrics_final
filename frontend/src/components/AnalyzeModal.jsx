import React, { useState } from 'react';
import { 
  X, Search, CheckCircle2, AlertCircle, Loader2, GitBranch, 
  Sliders, ArrowRight, Shield, RefreshCw, AlertTriangle, Info, Terminal
} from 'lucide-react';
import { validateRepository, startAnalysis } from '../api';

export default function AnalyzeModal({ isOpen, onClose, onAnalysisStarted }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationReport, setValidationReport] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [showWeightConfig, setShowWeightConfig] = useState(false);

  // Initial Configurable Research Weights
  const [weights, setWeights] = useState({
    complexity: 0.25,
    coupling: 0.20,
    maintainability: 0.20,
    churn: 0.15,
    activity: 0.10,
    defect: 0.10
  });

  if (!isOpen) return null;

  const handleValidate = async () => {
    if (!repoUrl.trim()) return;
    setIsValidating(true);
    setValidationReport(null);
    setValidationError(null);

    try {
      const report = await validateRepository(repoUrl.trim());
      if (report && (report.valid || report.is_valid)) {
        setValidationReport(report);
        setValidationError(null);
      } else {
        setValidationReport(null);
        setValidationError({
          error_code: report?.error_code || 'VALIDATION_FAILED',
          message: report?.message || report?.error_reason || 'Repository validation failed.',
          details: report?.details,
          suggestion: report?.suggestion || 'Please check that the repository is public and the URL or local path is correct.'
        });
      }
    } catch (err) {
      setValidationReport(null);
      setValidationError({
        error_code: 'CLIENT_ERROR',
        message: err.message || 'Error connecting to validation service.',
        details: err.stack,
        suggestion: 'Ensure the backend server is running and reachable.'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleStart = async () => {
    if (!repoUrl.trim()) return;
    setIsStarting(true);
    try {
      const res = await startAnalysis(repoUrl.trim(), showWeightConfig ? weights : null);
      onAnalysisStarted(res.project_id);
      onClose();
    } catch (err) {
      setValidationError({
        error_code: 'START_FAILED',
        message: err.message || 'Failed to start analysis run.',
        details: err.stack,
        suggestion: 'Please try again or check backend logs.'
      });
      setIsStarting(false);
    }
  };

  const sampleRepos = [
    { name: "Script (Target Repo)", url: "https://github.com/kasibhatlanavyatha25-alt/Script.git" },
    { name: "Apache Commons CLI", url: "https://github.com/apache/commons-cli" },
    { name: "Square JavaPoet", url: "https://github.com/square/javapoet" },
    { name: "Google Guice", url: "https://github.com/google/guice" }
  ];

  const isValid = validationReport && (validationReport.valid || validationReport.is_valid);
  const isAnalyzable = isValid && (
    validationReport.supported || 
    validationReport.has_analyzable_files || 
    validationReport.has_java_files ||
    (validationReport.source_file_count ?? 0) > 0
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl glass-panel-glow bg-slate-900 border border-slate-700 p-6 md:p-8 space-y-6 shadow-2xl my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Analyze Git Repository</h2>
              <p className="text-xs text-slate-400">Input public GitHub URL or local Git repository path (Java, Python, JS/TS supported)</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input Section */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Repository URL / Local Path
          </label>
          <div className="flex gap-2">
            <input 
              type="text" 
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                setValidationReport(null);
                setValidationError(null);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleValidate();
                }
              }}
              placeholder="e.g. https://github.com/owner/repo.git or C:\projects\my-repo"
              className="form-input text-sm flex-1 font-mono bg-slate-950 border-slate-700 focus:border-indigo-500 text-slate-100 px-3 py-2 rounded-lg border"
            />
            <button 
              onClick={handleValidate}
              disabled={isValidating || !repoUrl.trim()}
              className="btn-secondary px-4 py-2 shrink-0 cursor-pointer flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition"
            >
              {isValidating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              {isValidating ? 'Validating...' : 'Validate'}
            </button>
          </div>

          {/* Quick Preset Badges */}
          <div className="flex items-center gap-2 pt-1 flex-wrap">
            <span className="text-xs text-slate-500">Quick Test:</span>
            {sampleRepos.map((sr, idx) => (
              <button 
                key={idx}
                onClick={() => {
                  setRepoUrl(sr.url);
                  setValidationReport(null);
                  setValidationError(null);
                }}
                className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 font-mono transition-colors"
              >
                {sr.name}
              </button>
            ))}
          </div>
        </div>

        {/* Validation Error Feedback */}
        {validationError && (
          <div className="p-5 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-rose-200">Repository Validation Failed</span>
                    <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-rose-900/60 border border-rose-700 text-rose-300">
                      {validationError.error_code}
                    </span>
                  </div>
                  <p className="text-xs text-rose-200 font-medium mt-1">
                    {validationError.message}
                  </p>
                </div>
              </div>
              <button
                onClick={handleValidate}
                disabled={isValidating}
                className="px-2.5 py-1.5 text-xs bg-rose-900/80 hover:bg-rose-800 border border-rose-700 rounded text-rose-200 flex items-center gap-1.5 shrink-0 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />
                Retry
              </button>
            </div>

            {/* Error Details if present */}
            {validationError.details && (
              <div className="p-2.5 rounded bg-slate-950/80 border border-rose-900/60 font-mono text-[11px] text-rose-300/90 overflow-x-auto whitespace-pre-wrap">
                <div className="text-slate-400 text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Terminal className="w-3 h-3" /> Git Diagnostics / Details
                </div>
                {validationError.details}
              </div>
            )}

            {/* Possible Solution / Suggestion */}
            {validationError.suggestion && (
              <div className="flex items-start gap-2 text-xs text-amber-300/90 bg-amber-950/30 p-2.5 rounded border border-amber-800/40">
                <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-300">Possible solution:</span>{' '}
                  {validationError.suggestion}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Validation Success Feedback */}
        {isValid && (
          <div className="p-5 rounded-xl bg-indigo-950/30 border border-indigo-500/40 space-y-4">
            <div className="flex items-center justify-between border-b border-indigo-900/50 pb-3">
              <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ✓ Repository Validated
              </div>
              <span className="px-2.5 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-medium">
                {validationReport.version_strategy || 'Active Branch Analysis'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block">Repository</span>
                <span className="text-white font-bold text-sm truncate block mt-0.5">
                  {validationReport.repository_name || validationReport.repo_name}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block">Branch / HEAD</span>
                <span className="text-indigo-300 font-mono font-bold text-sm block mt-0.5 truncate">
                  {validationReport.default_branch || validationReport.branch || 'main'}
                  {validationReport.head_commit_short || validationReport.head_commit
                    ? ` (${(validationReport.head_commit_short || validationReport.head_commit).slice(0, 7)})`
                    : ''}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block">Commits</span>
                <span className="text-indigo-400 font-mono font-bold text-sm block mt-0.5">
                  {validationReport.commit_count ?? validationReport.total_commits ?? 0}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block">Source Files</span>
                <span className="text-cyan-400 font-mono font-bold text-sm block mt-0.5">
                  {validationReport.source_file_count ?? validationReport.analyzable_files_count ?? validationReport.total_java_files ?? 0}
                </span>
              </div>
            </div>

            {/* Active Analyzer Status Banner */}
            <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs flex items-center justify-between">
              <span className="text-slate-400 font-medium">Primary Language:</span>
              <span className="font-semibold text-indigo-300 font-mono">
                {validationReport.primary_language || 'Multi-Language'}
              </span>
            </div>

            {/* Detected Languages Breakdown */}
            {((validationReport.language_breakdown && Object.keys(validationReport.language_breakdown).length > 0) ||
              (validationReport.detected_languages && Object.keys(validationReport.detected_languages).length > 0) ||
              (validationReport.languages && validationReport.languages.length > 0)) && (
              <div className="space-y-1.5 text-xs">
                <span className="text-slate-400 font-semibold block">Languages & Source Breakdown:</span>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(validationReport.language_breakdown || validationReport.detected_languages || {}).map(([lang, count]) => {
                    const isAnalyzableLang = ['Java', 'Python', 'TypeScript', 'JavaScript', 'C/C++', 'Go', 'Rust'].includes(lang);
                    return (
                      <span 
                        key={lang} 
                        className={`px-2.5 py-1 rounded-full text-xs font-mono font-medium border ${
                          isAnalyzableLang
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-slate-800/90 text-slate-400 border-slate-700'
                        }`}
                      >
                        {lang}: <b>{count}</b>
                      </span>
                    );
                  })}
                  {(!validationReport.language_breakdown || Object.keys(validationReport.language_breakdown).length === 0) &&
                    validationReport.languages?.map((lang) => (
                      <span 
                        key={lang} 
                        className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      >
                        {lang}
                      </span>
                    ))}
                </div>
              </div>
            )}

            {/* Warning if no analyzable files */}
            {!isAnalyzable && (
              <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block">Compatible Analyzer Unavailable</span>
                  <p className="text-amber-200/90 mt-0.5">
                    {validationReport.warning_message || 'Repository validated successfully, but no compatible analyzer is currently available for this language.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Configurable Research Weights Accordion */}
        <div className="border border-slate-800 rounded-xl overflow-hidden">
          <button 
            type="button"
            onClick={() => setShowWeightConfig(!showWeightConfig)}
            className="w-full flex items-center justify-between p-3.5 bg-slate-950/60 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            <span className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              Configure Research ESDI Weights (Hypothesis Tuning)
            </span>
            <span className="text-indigo-400">{showWeightConfig ? 'Collapse' : 'Customize'}</span>
          </button>

          {showWeightConfig && (
            <div className="p-4 bg-slate-950/90 space-y-3 text-xs border-t border-slate-800">
              <p className="text-slate-400 italic">
                * Weights represent research hypotheses and sum to 1.0 (100%).
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {Object.keys(weights).map((key) => (
                  <div key={key} className="space-y-1">
                    <label className="capitalize text-slate-300 font-medium">{key} Weight: {(weights[key] * 100).toFixed(0)}%</label>
                    <input 
                      type="range" 
                      min="0" 
                      max="0.5" 
                      step="0.05"
                      value={weights[key]}
                      onChange={(e) => setWeights({ ...weights, [key]: parseFloat(e.target.value) })}
                      className="w-full accent-indigo-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
          <button 
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer"
          >
            Cancel
          </button>
          <button 
            type="button"
            onClick={handleStart}
            disabled={isStarting || !isValid}
            className={`px-6 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
              !isValid
                ? 'bg-slate-800 text-slate-500 border border-slate-700/50 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 cursor-pointer'
            }`}
            title={
              !isValid
                ? 'Please validate the repository first'
                : 'Start Evolutionary Software DNA Analysis'
            }
          >
            {isStarting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Initializing Pipeline...
              </>
            ) : (
              <>
                <span>Start Full Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
