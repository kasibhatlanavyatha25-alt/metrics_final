import React, { useState } from 'react';
import { DependencyGraphResponse, DependencyGraphNode } from '../types';
import { Network, CircleDot, ArrowRight } from 'lucide-react';

interface DependencyGraphProps {
  graph: DependencyGraphResponse | null;
  onSelectNode?: (node: DependencyGraphNode) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ graph, onSelectNode }) => {
  const [selectedNode, setSelectedNode] = useState<DependencyGraphNode | null>(null);

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="glass-card rounded-xl p-6 border border-slate-800 text-center text-slate-400">
        No graph nodes available.
      </div>
    );
  }

  // Generate deterministic circular or layered layout coordinates
  const width = 600;
  const height = 300;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 110;

  const nodePositions: Record<string, { x: number; y: number }> = {};
  graph.nodes.forEach((node, idx) => {
    if (node.id === 'PaymentService') {
      // Place main service in center
      nodePositions[node.id] = { x: centerX, y: centerY };
    } else {
      const angle = ((idx + 1) / (graph.nodes.length - 1)) * 2 * Math.PI;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    }
  });

  const handleNodeClick = (node: DependencyGraphNode) => {
    setSelectedNode(node);
    if (onSelectNode) onSelectNode(node);
  };

  return (
    <div className="glass-card rounded-xl p-5 border border-slate-800">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              NetworkX Class Dependency Graph
            </h2>
            <div className="text-xs text-slate-400">
              Nodes: <span className="text-sky-300 font-mono">{graph.total_nodes}</span> | Edges: <span className="text-indigo-300 font-mono">{graph.total_edges}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono">
          <span className="flex items-center gap-1 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Mutated Hotspot
          </span>
          <span className="flex items-center gap-1 text-indigo-400">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" /> Unchanged Class
          </span>
        </div>
      </div>

      <div className="relative mt-4 flex flex-col items-center justify-center bg-slate-950/60 rounded-lg p-2 border border-slate-800/60 overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64 select-none">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
            </marker>
            <marker id="arrow-active" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
            </marker>
          </defs>

          {/* Edges */}
          {graph.edges.map((edge, idx) => {
            const src = nodePositions[edge.source];
            const tgt = nodePositions[edge.target];
            if (!src || !tgt) return null;
            const isHighlighted = selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);

            return (
              <line
                key={idx}
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke={isHighlighted ? '#f43f5e' : '#334155'}
                strokeWidth={isHighlighted ? 2 : 1}
                strokeDasharray={edge.dependency_type === 'inheritance' ? '4 2' : undefined}
                markerEnd={isHighlighted ? 'url(#arrow-active)' : 'url(#arrow)'}
              />
            );
          })}

          {/* Nodes */}
          {graph.nodes.map((node) => {
            const pos = nodePositions[node.id] || { x: 50, y: 50 };
            const isMain = node.id === 'PaymentService';
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => handleNodeClick(node)}
                className="cursor-pointer group"
              >
                <circle
                  r={isMain ? 18 : 12}
                  fill={isMain ? '#f43f5e' : node.is_changed ? '#f59e0b' : '#3b82f6'}
                  fillOpacity={0.85}
                  stroke={isSelected ? '#ffffff' : '#1e293b'}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  className="transition-all duration-200 group-hover:scale-110"
                />
                <text
                  y={isMain ? 28 : 22}
                  textAnchor="middle"
                  fill="#e2e8f0"
                  fontSize={isMain ? "10px" : "8.5px"}
                  fontFamily="monospace"
                  fontWeight={isMain ? "bold" : "normal"}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Bar */}
        {selectedNode && (
          <div className="w-full mt-2 bg-slate-900/90 rounded p-2.5 border border-slate-700 text-xs font-mono flex items-center justify-between">
            <div>
              <span className="text-slate-400">Class: </span>
              <span className="text-sky-300 font-bold">{selectedNode.label}</span>
              <span className="text-slate-500 ml-2">({selectedNode.package})</span>
            </div>
            {selectedNode.metrics && (
              <div className="text-slate-300 flex items-center gap-3 text-[11px]">
                <span>LOC: <b className="text-white">{selectedNode.metrics.loc}</b></span>
                <span>CC: <b className="text-rose-400">{selectedNode.metrics.cc}</b></span>
                <span>WMC: <b className="text-amber-400">{selectedNode.metrics.wmc}</b></span>
                <span>CBO: <b className="text-sky-400">{selectedNode.metrics.cbo}</b></span>
                <span>LCOM: <b className="text-purple-400">{selectedNode.metrics.lcom.toFixed(2)}</b></span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
