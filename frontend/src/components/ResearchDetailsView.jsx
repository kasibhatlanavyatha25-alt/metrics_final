import React from 'react';
import { 
  BookOpen, Dna, ShieldAlert, Cpu, Activity, 
  Target, Layers, HelpCircle, AlertCircle
} from 'lucide-react';

export default function ResearchDetailsView() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Title */}
      <div className="glass-panel p-8 border-indigo-500/30 space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge badge-moderate font-mono">Academic Methodology & Formal Framework</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">
          AI-Based Software Metrics Recommendation System using Evolutionary Software DNA
        </h1>
        <p className="text-sm text-slate-300 leading-relaxed">
          Comprehensive documentation of mathematical formulations, AST extraction algorithms, Evolutionary DNA modeling, mutation thresholds, ESDI normalization, and explainability mechanisms for peer review and academic evaluation.
        </p>
      </div>

      {/* 1. Metrics & AST Extraction */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          1. Chidamber & Kemerer (CK) & Object-Oriented Metrics Definitions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">1. Lines of Code (LOC)</span>
            <p className="text-slate-300 leading-relaxed">
              Count of non-blank, non-comment source lines of code in each class file.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">2. Weighted Methods per Class (WMC)</span>
            <p className="text-slate-300 leading-relaxed">
              Sum of cyclomatic complexities of all member methods and constructors declared in the class.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">3. Coupling Between Objects (CBO)</span>
            <p className="text-slate-300 leading-relaxed">
              Count of distinct non-primitive reference types/classes to which a class is coupled via field types, parameters, return types, and imports.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">4. Response For a Class (RFC)</span>
            <p className="text-slate-300 leading-relaxed">
              Number of methods in the class plus the count of unique external methods directly invoked by its methods.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">5. Lack of Cohesion of Methods (LCOM)</span>
            <p className="text-slate-300 leading-relaxed">
              Henderson-Sellers formulation measuring the degree to which methods operate on disjoint subsets of instance fields (0.0 = high cohesion, 1.0 = total lack of cohesion).
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">6. Depth of Inheritance Tree (DIT)</span>
            <p className="text-slate-300 leading-relaxed">
              Maximum length from the class node to the root class (`Object`) in the project inheritance hierarchy.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">7. Number of Children (NOC)</span>
            <p className="text-slate-300 leading-relaxed">
              Count of direct subclasses that inherit from the class within the project workspace.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-indigo-300 font-mono text-sm block">8. McCabe Cyclomatic Complexity (CC)</span>
            <p className="text-slate-300 leading-relaxed">
              Quantitative measure of independent linear paths through control flow decisions (if, while, for, case, catch, ternary).
            </p>
          </div>
        </div>
      </div>

      {/* 2. Evolutionary Software DNA Concept */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
          <Dna className="w-5 h-5 text-cyan-400" />
          2. Evolutionary Software DNA Model (Analytical Representation D_t = (V_t, E_t, M_t))
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          Per Patent Specification IDF-B (Equation 1), the Evolutionary Software DNA construct strictly consists of AST nodes V_t, dependency edges E_t, and normalized metric matrix M_t over the 5 canonical structural metrics:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs font-mono">
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-indigo-400 font-bold block">1. LOC Gene</span>
            <span className="text-slate-400 text-[11px]">Lines of Code Volume</span>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-cyan-400 font-bold block">2. CC Gene</span>
            <span className="text-slate-400 text-[11px]">Cyclomatic Complexity</span>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold block">3. WMC Gene</span>
            <span className="text-slate-400 text-[11px]">Weighted Methods per Class</span>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-purple-400 font-bold block">4. CBO Gene</span>
            <span className="text-slate-400 text-[11px]">Coupling Between Objects</span>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <span className="text-amber-400 font-bold block">5. LCOM Gene</span>
            <span className="text-slate-400 text-[11px]">Lack of Cohesion of Methods</span>
          </div>
        </div>
      </div>

      {/* 3. DNA Mutation Formulas */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          3. Software DNA Mutation Analysis & Classification
        </h2>
        <div className="space-y-3 text-xs text-slate-300">
          <p>
            A Software DNA Mutation represents a significant shift in a metric between two consecutive version snapshots (V<sub>t-1</sub> → V<sub>t</sub>):
          </p>
          <div className="p-4 rounded-xl bg-slate-950 font-mono text-slate-200 border border-slate-800 space-y-2">
            <div>Δ = Current_Value - Previous_Value</div>
            <div>Percentage Change (%) = ((Current_Value - Previous_Value) / |Previous_Value|) × 100</div>
          </div>
          <p className="font-semibold text-slate-200">Severity Threshold Rules:</p>
          <ul className="list-disc list-inside space-y-1 text-slate-400 pl-2">
            <li><b className="text-emerald-400">HEALTHY</b>: Metric change represents architectural improvement or minor drift within normal tolerance (&lt; +20%).</li>
            <li><b className="text-amber-400">RISKY</b>: Metric deterioration between +20% and +45% across versions.</li>
            <li><b className="text-rose-400">CRITICAL</b>: Metric deterioration exceeding +45% (or rapid LOC surge &gt; 75%) or simultaneous degradation across multiple metrics (Combined Mutation).</li>
          </ul>
        </div>
      </div>

      {/* 4. ESDI Formula & Configurable Weights */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
          <Activity className="w-5 h-5 text-amber-400" />
          4. Evolutionary Software DNA Index (ESDI) & Normalization
        </h2>
        <div className="space-y-3 text-xs text-slate-300">
          <p>
            The ESDI is a normalized 0–100 evolutionary risk score aggregating historical quality trends:
          </p>
          <div className="p-4 rounded-xl bg-slate-950 font-mono text-amber-300 border border-slate-800">
            ESDI = 0.25·ComplexityRisk + 0.20·CouplingRisk + 0.20·MaintainabilityRisk + 0.15·ChurnRisk + 0.10·ActivityRisk + 0.10·DefectRisk
          </div>
          <div className="p-4 rounded-xl bg-slate-950 font-mono text-emerald-300 border border-slate-800">
            Software Health Score = 100 - ESDI
          </div>
          <p className="italic text-slate-400">
            * Research Notice: ESDI weights are configurable research hypotheses. If historical defect logs are unavailable, the 10% defect weight is redistributed proportionally across the remaining 5 factors without inventing synthetic defect counts.
          </p>
        </div>
      </div>
    </div>
  );
}
