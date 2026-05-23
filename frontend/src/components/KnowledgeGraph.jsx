import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2Layout from 'graphology-layout-forceatlas2/worker';

const DEFAULT_COLOR = '#888888';

// ── Helper: build a Graphology graph from API data ──────────────────
function buildGraph(graphData, hiddenClusters) {
  const graph = new Graph({ multi: false, type: 'undirected' });
  if (!graphData?.nodes?.length) return graph;

  const visibleNodes = new Set();

  graphData.nodes.forEach((node) => {
    if (hiddenClusters.has(node.community)) return;

    const name = node.name || node.id;
    if (graph.hasNode(name)) return;

    // Size by centrality (InfraNodus-style), fallback to frequency
    const centrality = node.centrality || 0;
    const frequency = node.frequency || 1;
    const baseSize = Math.max(centrality * 120, Math.log2(frequency + 1) * 2.5, 3);
    const size = Math.min(Math.max(baseSize, 3), 22);

    graph.addNode(name, {
      label: name,
      size,
      color: node.community_color || DEFAULT_COLOR,
      x: Math.random() * 100,
      y: Math.random() * 100,
      // Store original data for click handling
      _data: node,
    });
    visibleNodes.add(name);
  });

  (graphData.edges || []).forEach((edge, i) => {
    const src = typeof edge.source === 'object' ? edge.source.name || edge.source.id : edge.source;
    const tgt = typeof edge.target === 'object' ? edge.target.name || edge.target.id : edge.target;

    if (!visibleNodes.has(src) || !visibleNodes.has(tgt)) return;
    if (src === tgt) return;
    if (graph.hasEdge(src, tgt)) return;

    const weight = edge.weight || 1;
    graph.addEdge(src, tgt, {
      weight,
      size: Math.min(Math.log2(weight + 1) * 0.6, 3),
      color: 'rgba(255,255,255,0.08)',
      _type: edge.type || '',
    });
  });

  return graph;
}

// ── Main Component ──────────────────────────────────────────────────
const KnowledgeGraph = ({ graphData, onNodeClick, hiddenClusters = new Set() }) => {
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const layoutRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  // Build the graph whenever data or filters change
  const graph = useMemo(
    () => buildGraph(graphData, hiddenClusters),
    [graphData, hiddenClusters]
  );

  // Initialize Sigma and layout
  useEffect(() => {
    if (!containerRef.current || graph.order === 0) return;

    // Clean up previous instance
    if (sigmaRef.current) {
      sigmaRef.current.kill();
      sigmaRef.current = null;
    }
    if (layoutRef.current) {
      layoutRef.current.kill();
      layoutRef.current = null;
    }

    // Force clear the container to prevent overlapping canvases when switching documents
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
    }

    // Run synchronous FA2 for initial layout (fast pass)
    forceAtlas2.assign(graph, {
      iterations: 100,
      settings: {
        gravity: 1,
        scalingRatio: 2,
        barnesHutOptimize: true,
        strongGravityMode: true,
        slowDown: 5,
      },
    });

    // Create Sigma instance
    const renderer = new Sigma(graph, containerRef.current, {
      allowInvalidContainer: true,
      renderEdgeLabels: false,
      labelFont: 'Inter, sans-serif',
      labelSize: 12,
      labelWeight: '500',
      labelColor: { color: '#000000' },
      labelDensity: 0.6,
      labelGridCellSize: 80,
      labelRenderedSizeThreshold: 4,
      defaultEdgeType: 'line',
      edgeLabelFont: 'Inter, sans-serif',
      stagePadding: 30,
      minCameraRatio: 0.08,
      maxCameraRatio: 8,
      // Node rendering
      nodeReducer: (node, data) => {
        const res = { ...data };

        if (hoveredNode) {
          // If a node is hovered, highlight it and its neighbors
          if (node === hoveredNode || graph.hasEdge(node, hoveredNode) || graph.hasEdge(hoveredNode, node)) {
            res.highlighted = true;
            res.zIndex = 1;
          } else {
            res.color = 'rgba(255,255,255,0.06)';
            res.label = '';
            res.zIndex = 0;
          }
        }

        return res;
      },
      // Edge rendering
      edgeReducer: (edge, data) => {
        const res = { ...data };

        if (hoveredNode) {
          const [src, tgt] = graph.extremities(edge);
          if (src === hoveredNode || tgt === hoveredNode) {
            res.color = 'rgba(255,255,255,0.5)';
            res.size = Math.max(data.size || 1, 1.5);
            res.zIndex = 1;
          } else {
            res.color = 'rgba(255,255,255,0.02)';
            res.hidden = true;
          }
        }

        return res;
      },
    });

    sigmaRef.current = renderer;

    // Start async FA2 layout for refinement
    const fa2 = new FA2Layout(graph, {
      settings: {
        gravity: 0.8,
        scalingRatio: 3,
        barnesHutOptimize: true,
        strongGravityMode: true,
        slowDown: 8,
      },
    });
    fa2.start();
    layoutRef.current = fa2;

    // Stop layout after convergence
    setTimeout(() => {
      if (layoutRef.current) {
        layoutRef.current.stop();
      }
    }, 4000);

    // Event: click
    renderer.on('clickNode', ({ node }) => {
      const nodeData = graph.getNodeAttributes(node);
      if (onNodeClick) {
        onNodeClick({
          name: node,
          id: nodeData._data?.id || node,
          ...nodeData._data,
        });
      }
      // Center camera on clicked node
      const pos = renderer.getNodeDisplayData(node);
      if (pos) {
        renderer.getCamera().animate(
          { x: pos.x, y: pos.y, ratio: 0.3 },
          { duration: 600 }
        );
      }
    });

    // Event: hover
    renderer.on('enterNode', ({ node }) => {
      setHoveredNode(node);
      containerRef.current.style.cursor = 'pointer';
    });

    renderer.on('leaveNode', () => {
      setHoveredNode(null);
      containerRef.current.style.cursor = 'default';
    });

    // Zoom to fit
    setTimeout(() => {
      renderer.getCamera().animate(
        { x: 0.5, y: 0.5, ratio: 1 },
        { duration: 500 }
      );
    }, 500);

    return () => {
      if (layoutRef.current) {
        layoutRef.current.kill();
        layoutRef.current = null;
      }
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [graph, onNodeClick]);

  // Update reducers when hover state changes (need to refresh sigma)
  useEffect(() => {
    if (sigmaRef.current) {
      sigmaRef.current.setSetting('nodeReducer', (node, data) => {
        const res = { ...data };
        if (hoveredNode) {
          if (
            node === hoveredNode ||
            graph.hasEdge(node, hoveredNode) ||
            graph.hasEdge(hoveredNode, node)
          ) {
            res.highlighted = true;
            res.zIndex = 1;
          } else {
            res.color = 'rgba(255,255,255,0.06)';
            res.label = '';
            res.zIndex = 0;
          }
        }
        return res;
      });

      sigmaRef.current.setSetting('edgeReducer', (edge, data) => {
        const res = { ...data };
        if (hoveredNode) {
          const [src, tgt] = graph.extremities(edge);
          if (src === hoveredNode || tgt === hoveredNode) {
            res.color = 'rgba(255,255,255,0.5)';
            res.size = Math.max(data.size || 1, 1.5);
            res.zIndex = 1;
          } else {
            res.color = 'rgba(255,255,255,0.02)';
            res.hidden = true;
          }
        }
        return res;
      });

      sigmaRef.current.refresh();
    }
  }, [hoveredNode, graph]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        height: '100%', color: 'var(--text-secondary)',
      }}>
        No graph data available. Upload a document or paste text to generate a Knowledge Graph.
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        background: 'transparent',
      }}
    />
  );
};

export default KnowledgeGraph;
