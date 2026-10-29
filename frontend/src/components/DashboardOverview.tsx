import React from 'react';
import {
  PipelineStatusResponse,
  DnaHistoryResponse,
  ClassMutationAnalysis,
  DependencyGraphResponse,
  CommitInfo,
} from '../types';
import { MetricCard } from './MetricCard';
import { EsdiGauge } from './EsdiGauge';
import { PipelineStatus } from './PipelineStatus';
import { CommitTimeline } from './CommitTimeline';
import { DnaTrajectoryViewer } from './DnaTrajectoryViewer';
import { MutationMatrix } from './MutationMatrix';
import { DependencyGraph } from './DependencyGraph';
import {
  Activity,
  AlertOctagon,
  Boxes,
  FileDiff,
  Database,
} from 'lucide-react';

interface DashboardOverviewProps {
  pipeline: PipelineStatusResponse;
  dnaHistory: DnaHistoryResponse | null;
  mutations: Record<string, ClassMutationAnalysis>;
  graph: DependencyGraphResponse | null;
  selectedCommit: CommitInfo | null;
  onSelectCommit: (commit: CommitInfo) => void;
  onOpenRemediation: () => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  pipeline,
  dnaHistory,
  mutations,
  graph,
  selectedCommit,
  onSelectCommit,
  onOpenRemediation,
}) => {
  const latestEsdi = pipeline.esdi;
  const isBlocked = latestEsdi.decision === 'BLOCK' || latestEsdi.decision === 'CRITICAL BLOCK';
  const targetClassName = 'PaymentService';
  const classMutation = mutations[targetClassName];
  const classMetrics = dnaHistory?.latest_metrics;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="ESDI Score"
          value={latestEsdi.esdi.toFixed(1)}
          subtitle="System DNA Index"
          glowColor={isBlocked ? 'danger' : latestEsdi.decision === 'WARN' ? 'warning' : 'success'}
          icon={<Activity className={`w-5 h-5 ${isBlocked ? 'text-rose-400' : 'text-emerald-400'}`} />}
          trend={{
            value: isBlocked ? 'HIGH DEVIATION' : 'STABLE',
            positive: !isBlocked,
          }}
        />

        <MetricCard
          title="5D Mutations"
          value={latestEsdi.mutation_count}
          subtitle="Severe Mutated Metrics"
          glowColor={latestEsdi.mutation_count > 0 ? 'danger' : 'success'}
          icon={<AlertOctagon className="w-5 h-5 text-rose-400" />}
          trend={{
            value: `${latestEsdi.mutation_count} Detected`,
            positive: latestEsdi.mutation_count === 0,
          }}
        />

        <MetricCard
          title="Affected Modules"
          value={latestEsdi.affected_modules.length}
          subtitle="Hotspot Classes"
          glowColor={latestEsdi.affected_modules.length > 0 ? 'warning' : 'primary'}
          icon={<Boxes className="w-5 h-5 text-sky-400" />}
        />

        <MetricCard
          title="Changed Files"
          value={pipeline.incremental_stats.files_changed}
          subtitle={`Out of ${pipeline.incremental_stats.files_total} Total Files`}
          glowColor="primary"
          icon={<FileDiff className="w-5 h-5 text-indigo-400" />}
        />

        <MetricCard
          title="AST Cache Hit Rate"
          value={`${pipeline.incremental_stats.cache_hit_rate}%`}
          subtitle={`${pipeline.incremental_stats.files_reused_from_cache} Reused / ${pipeline.incremental_stats.files_parsed} Parsed`}
          glowColor="success"
          icon={<Database className="w-5 h-5 text-emerald-400" />}
        />
      </div>

      {/* Main Section: Gauge & Gate Decision */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <EsdiGauge
            score={latestEsdi.esdi}
            decision={latestEsdi.decision}
            aggregateRisk={latestEsdi.aggregate_risk}
          />
        </div>
        <div className="lg:col-span-2">
          <PipelineStatus
            esdi={latestEsdi}
            onOpenRemediation={onOpenRemediation}
          />
        </div>
      </div>

      {/* Commit History & Incremental AST Analysis Bar */}
      <CommitTimeline
        commits={pipeline.all_commits}
        selectedCommitSha={selectedCommit?.sha || pipeline.latest_commit.sha}
        onSelectCommit={onSelectCommit}
        stats={pipeline.incremental_stats}
      />

      {/* Middle Section: DNA Trajectory & Dependency Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DnaTrajectoryViewer
          trajectory={dnaHistory?.records || []}
          className={targetClassName}
        />
        <DependencyGraph graph={graph} />
      </div>

      {/* 5-Dimensional Mutation Matrix */}
      <MutationMatrix
        mutationAnalysis={classMutation}
        currentMetrics={classMetrics}
        className={targetClassName}
      />
    </div>
  );
};
