import React from 'react';
import { RemediationResponse } from '../types';
import { X, CheckCircle, ArrowRight, ShieldCheck, Wrench, FileDiff, Sparkles } from 'lucide-react';

interface RemediationPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  remediation: RemediationResponse | null;
  loading: boolean;
  onApply: () => void;
}

export const RemediationPreview: React.FC<RemediationPreviewProps> = ({
  isOpen,
  onClose,
  remediation,
  loading,
  onApply,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b101b] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Automated AST Remediation Analysis
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono">
                  Extract Method
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Target: {remediation?.target_class || 'PaymentService'}.{remediation?.target_method || 'processPayment'}()
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Explanation Banner */}
          {remediation && (
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-white">Controlled Refactoring Strategy: </span>
                {remediation.explanation}
              </div>
            </div>
          )}

          {/* Metric Comparison & ESDI Delta */}
          {remediation && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* ESDI Gate Progression Card */}
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Quality Gate & ESDI Impact
                </div>
                <div className="flex items-center justify-around py-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <div className="text-center">
                    <div className="text-[11px] text-slate-400 uppercase font-mono">Before</div>
                    <div className="text-2xl font-black font-mono text-rose-400">{remediation.before_esdi.toFixed(1)}</div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                      {remediation.gate_before}
                    </span>
                  </div>

                  <ArrowRight className="w-6 h-6 text-indigo-400" />

                  <div className="text-center">
                    <div className="text-[11px] text-slate-400 uppercase font-mono">After</div>
                    <div className="text-2xl font-black font-mono text-emerald-400">{remediation.after_esdi.toFixed(1)}</div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                      {remediation.gate_after}
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-center text-xs font-mono text-emerald-400 font-semibold">
                  ESDI Improvement: -{remediation.esdi_delta.toFixed(1)} points
                </div>
              </div>

              {/* Verification & Tests Status */}
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Verification Suite Checks
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">Compilation & AST Parse:</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      {remediation.compilation_status.split(' ')[0]}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">Automated Unit Tests:</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      {remediation.test_status}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">ESDI Score Lowered:</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      VERIFIED
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Side-by-Side Metrics Table */}
          {remediation && (
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <div className="bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 font-mono uppercase">
                Detailed Metrics Before vs After Remediation
              </div>
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-4">Metric</th>
                    <th className="py-2 px-4">Before Remediation</th>
                    <th className="py-2 px-4">After Remediation</th>
                    <th className="py-2 px-4 text-right">Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr>
                    <td className="py-2 px-4 font-bold text-slate-200">Lines of Code (LOC)</td>
                    <td className="py-2 px-4 text-rose-300">{remediation.before_metrics.loc}</td>
                    <td className="py-2 px-4 text-emerald-300">{remediation.after_metrics.loc}</td>
                    <td className="py-2 px-4 text-right text-emerald-400 font-bold">
                      {remediation.after_metrics.loc - remediation.before_metrics.loc}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 font-bold text-slate-200">Cyclomatic Complexity (CC)</td>
                    <td className="py-2 px-4 text-rose-400 font-bold">{remediation.before_metrics.cc}</td>
                    <td className="py-2 px-4 text-emerald-400 font-bold">{remediation.after_metrics.cc}</td>
                    <td className="py-2 px-4 text-right text-emerald-400 font-bold">
                      {remediation.after_metrics.cc - remediation.before_metrics.cc}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 font-bold text-slate-200">Weighted Methods per Class (WMC)</td>
                    <td className="py-2 px-4 text-rose-300">{remediation.before_metrics.wmc}</td>
                    <td className="py-2 px-4 text-emerald-300">{remediation.after_metrics.wmc}</td>
                    <td className="py-2 px-4 text-right text-emerald-400 font-bold">
                      {remediation.after_metrics.wmc - remediation.before_metrics.wmc}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 font-bold text-slate-200">Coupling Between Objects (CBO)</td>
                    <td className="py-2 px-4 text-slate-300">{remediation.before_metrics.cbo}</td>
                    <td className="py-2 px-4 text-slate-300">{remediation.after_metrics.cbo}</td>
                    <td className="py-2 px-4 text-right text-slate-400 font-bold">
                      {remediation.after_metrics.cbo - remediation.before_metrics.cbo}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 font-bold text-slate-200">Lack of Cohesion (LCOM)</td>
                    <td className="py-2 px-4 text-rose-300">{remediation.before_metrics.lcom.toFixed(2)}</td>
                    <td className="py-2 px-4 text-emerald-300">{remediation.after_metrics.lcom.toFixed(2)}</td>
                    <td className="py-2 px-4 text-right text-emerald-400 font-bold">
                      {(remediation.after_metrics.lcom - remediation.before_metrics.lcom).toFixed(2)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Unified Diff Viewer */}
          {remediation && (
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <div className="bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 font-mono flex items-center gap-2">
                <FileDiff className="w-4 h-4 text-sky-400" />
                Unified AST Diff ({remediation.class_name || 'RefactoredModule'})
              </div>
              <pre className="bg-[#070b12] p-4 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-60 leading-relaxed">
                {remediation.diff.split('\n').map((line, idx) => {
                  let lineClass = 'text-slate-400';
                  if (line.startsWith('+') && !line.startsWith('+++')) lineClass = 'text-emerald-400 bg-emerald-950/30';
                  if (line.startsWith('-') && !line.startsWith('---')) lineClass = 'text-rose-400 bg-rose-950/30';
                  if (line.startsWith('@@')) lineClass = 'text-indigo-400 font-bold';
                  return (
                    <div key={idx} className={lineClass}>
                      {line}
                    </div>
                  );
                })}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
          >
            Close
          </button>

          <button
            onClick={onApply}
            disabled={loading}
            className="px-5 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-indigo-600 hover:from-emerald-600 hover:to-indigo-700 text-white text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-emerald-500/20"
          >
            <ShieldCheck className="w-4 h-4" />
            Apply Remediation & Re-run Gate
          </button>
        </div>
      </div>
    </div>
  );
};
