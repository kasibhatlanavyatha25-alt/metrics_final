import React, { useState, useEffect } from 'react';
import { 
  Dna, Search, Layers, FileCode2, ShieldAlert, Activity, 
  Sparkles, TrendingUp, History, BookOpen, Menu, X, PlusCircle, AlertCircle,
  Terminal, ShieldCheck
} from 'lucide-react';

import LandingView from './components/LandingView';
import AnalyzeModal from './components/AnalyzeModal';
import ProgressView from './components/ProgressView';
import DashboardOverview from './components/DashboardOverview';
import SoftwareMetricsView from './components/SoftwareMetricsView';
import EvolutionaryDNAView from './components/EvolutionaryDNAView';
import DNAMutationView from './components/DNAMutationView';
import ESDIAnalysisView from './components/ESDIAnalysisView';
import ModuleRiskView from './components/ModuleRiskView';
import RecommendationsView from './components/RecommendationsView';
import FuturePredictionView from './components/FuturePredictionView';
import DiagnosticsView from './components/DiagnosticsView';
import HistoryView from './components/HistoryView';
import ResearchDetailsView from './components/ResearchDetailsView';

import { fetchProjectsList, fetchProjectDashboard } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('landing');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [progressProjectId, setProgressProjectId] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [projectsList, setProjectsList] = useState([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Load existing projects on start
  const refreshProjects = async () => {
    try {
      const projs = await fetchProjectsList();
      setProjectsList(projs);
      if (projs.length > 0 && !activeProjectId) {
        // do not auto select so landing page is first
      }
    } catch (err) {
      console.error('Error fetching projects:', err);
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  // Load active project dashboard data when activeProjectId changes
  useEffect(() => {
    if (activeProjectId) {
      fetchProjectDashboard(activeProjectId)
        .then(data => setDashboardData(data))
        .catch(err => console.error('Error loading dashboard:', err));
    }
  }, [activeProjectId]);

  const handleStartNewAnalysis = () => {
    setIsModalOpen(true);
  };

  const handleAnalysisStarted = (newProjectId) => {
    setProgressProjectId(newProjectId);
    setActiveTab('progress');
  };

  const handleAnalysisComplete = (completedProjectId) => {
    setProgressProjectId(null);
    setActiveProjectId(completedProjectId);
    setActiveTab('dashboard');
    refreshProjects();
  };

  const handleSelectProject = (projId) => {
    setActiveProjectId(projId);
    setActiveTab('dashboard');
  };

  const navItems = [
    { id: 'landing', label: 'Home / Architecture', icon: Layers },
    { id: 'dashboard', label: 'Project Overview', icon: Activity, requiresProject: true },
    { id: 'diagnostics', label: 'Diagnostics & Proof', icon: Terminal, requiresProject: true },
    { id: 'metrics', label: 'Software Quality Metrics', icon: FileCode2, requiresProject: true },
    { id: 'dna', label: 'Evolutionary Software DNA', icon: Dna, requiresProject: true },
    { id: 'mutations', label: 'DNA Mutation Analysis', icon: ShieldAlert, requiresProject: true },
    { id: 'esdi', label: 'ESDI Risk Index', icon: Activity, requiresProject: true },
    { id: 'risks', label: 'Module / Source Unit Risk Analysis', icon: ShieldAlert, requiresProject: true },
    { id: 'recommendations', label: 'AI Recommendations', icon: Sparkles, requiresProject: true },
    { id: 'prediction', label: 'Future Prediction', icon: TrendingUp, requiresProject: true },
    { id: 'history', label: 'Analysis History', icon: History },
    { id: 'research', label: 'Research Details', icon: BookOpen },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Top Main Navigation Header */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-slate-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div 
            onClick={() => setActiveTab('landing')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Dna className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
                Software DNA Engine
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-400 border border-indigo-500/30">
                v1.0-research
              </span>
            </div>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-3">
          {activeProjectId && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-400">Active:</span>
              <span className="font-semibold text-white truncate max-w-[150px]">
                {dashboardData?.top_cards?.project_name || `Project #${activeProjectId}`}
              </span>
            </div>
          )}

          <button
            onClick={handleStartNewAnalysis}
            className="btn-primary text-xs flex items-center gap-1.5 shadow-lg shadow-indigo-500/20 cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Analyze Git Repository</span>
          </button>
        </div>
      </header>

      {/* Main App Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-slate-950/95 lg:bg-slate-950/50 backdrop-blur-md
          border-r border-slate-800/80 p-4 flex flex-col justify-between
          transition-transform duration-300 ease-in-out
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <div className="space-y-6">
            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3">
                Evolutionary Analysis
              </span>
              <nav className="space-y-1 mt-2">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isDisabled = item.requiresProject && !activeProjectId;
                  const isActive = activeTab === item.id;

                  return (
                    <button
                      key={item.id}
                      disabled={isDisabled}
                      onClick={() => {
                        setActiveTab(item.id);
                        setMobileMenuOpen(false);
                      }}
                      className={`
                        w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium
                        transition-all duration-200 text-left cursor-pointer
                        ${isActive 
                          ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm shadow-indigo-500/10' 
                          : isDisabled
                          ? 'text-slate-600 cursor-not-allowed opacity-50'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                        }
                      `}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                      <span className="flex-1 truncate">{item.label}</span>
                      {isDisabled && (
                        <span className="text-[9px] text-slate-600 font-mono">No Repo</span>
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Sidebar Footer Info */}
          <div className="pt-4 border-t border-slate-800/60 text-xs text-slate-500 space-y-2">
            <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60 space-y-1">
              <span className="font-semibold text-slate-300 block">Formal Project Title</span>
              <p className="text-[10px] leading-tight text-slate-400">
                AI-Based Software Metrics Recommendation System using Evolutionary Software DNA
              </p>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full overflow-y-auto">
          {activeTab === 'landing' && (
            <LandingView 
              onStartNew={handleStartNewAnalysis}
              onSelectProject={handleSelectProject}
              existingProjects={projectsList}
            />
          )}

          {activeTab === 'progress' && progressProjectId && (
            <ProgressView 
              projectId={progressProjectId}
              onComplete={handleAnalysisComplete}
              onCancel={() => setActiveTab('landing')}
            />
          )}

          {activeTab === 'dashboard' && activeProjectId && (
            <DashboardOverview 
              data={dashboardData}
              onNavigateTab={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'diagnostics' && activeProjectId && (
            <DiagnosticsView 
              project={projectsList.find(p => p.id === activeProjectId) || { id: activeProjectId }}
              onNavigateTab={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'metrics' && activeProjectId && (
            <SoftwareMetricsView projectId={activeProjectId} />
          )}

          {activeTab === 'dna' && activeProjectId && (
            <EvolutionaryDNAView projectId={activeProjectId} />
          )}

          {activeTab === 'mutations' && activeProjectId && (
            <DNAMutationView projectId={activeProjectId} />
          )}

          {activeTab === 'esdi' && activeProjectId && (
            <ESDIAnalysisView projectId={activeProjectId} />
          )}

          {activeTab === 'risks' && activeProjectId && (
            <ModuleRiskView projectId={activeProjectId} />
          )}

          {activeTab === 'recommendations' && activeProjectId && (
            <RecommendationsView projectId={activeProjectId} />
          )}

          {activeTab === 'prediction' && activeProjectId && (
            <FuturePredictionView projectId={activeProjectId} />
          )}

          {activeTab === 'history' && (
            <HistoryView 
              onSelectProject={handleSelectProject}
              activeProjectId={activeProjectId}
            />
          )}

          {activeTab === 'research' && (
            <ResearchDetailsView />
          )}
        </main>
      </div>

      {/* Repository Analysis Modal */}
      <AnalyzeModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAnalysisStarted={handleAnalysisStarted}
      />
    </div>
  );
}
