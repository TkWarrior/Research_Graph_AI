import React, { useEffect, useRef, useState, useCallback } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import FA2Layout from 'graphology-layout-forceatlas2/worker';
import { api } from '../services/api';

const DEFAULT_COLOR = '#888888';

// ── Color palette for new nodes that appear during expansion ─────────
const EXPAND_FLASH_COLOR = 'rgba(136, 211, 206, 0.95)';

// ── Curated palette: one color per known entity type ─────────────────
const TYPE_COLORS = {
  PERSON:        '#FF6B9D', // pink-red
  ORGANIZATION:  '#4D96FF', // blue
  CONCEPT:       '#88d3ce', // teal
  LOCATION:      '#FFD166', // amber
  EVENT:         '#FF9F43', // orange
  TECHNOLOGY:    '#A29BFE', // lavender
  PRODUCT:       '#55EFC4', // mint
  DATE:          '#FD79A8', // rose
  WORK:          '#FFEAA7', // yellow
  OTHER:         '#B2BEC3', // slate
};

// Fallback: deterministic color from node name when type is absent/unknown
const HASH_PALETTE = [
  '#FF6B9D', '#4D96FF', '#88d3ce', '#FFD166', '#FF9F43',
  '#A29BFE', '#55EFC4', '#FD79A8', '#74B9FF', '#00CEC9',
  '#6C5CE7', '#FDCB6E', '#E17055', '#81ECEC', '#DFE6E9',
];

function hashColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
  }
  return HASH_PALETTE[hash % HASH_PALETTE.length];
}

// Pick the best color for a node: community_color > type map > name hash
function resolveNodeColor(node) {
  if (node.community_color) return node.community_color;
  const type = (node.type || '').toUpperCase();
  return TYPE_COLORS[type] || hashColor(node.name || node.id || 'x');
}


// ── Merge incoming API data into the persistent Graphology graph ─────
// pivotPos: { x, y } — new nodes spawn near this position so they don't
// appear across the canvas. Falls back to center (50, 50) if not provided.
function mergeIntoGraph(graph, apiData, expandedNodes, pivotPos = null) {
  const added = { nodes: [], edges: [] };
  if (!apiData?.nodes) return added;

  // Tight spawn radius keeps new nodes visually close to the clicked node.
  const baseX = pivotPos ? pivotPos.x : 50;
  const baseY = pivotPos ? pivotPos.y : 50;
  const spread = pivotPos ? 8 : 100;

  apiData.nodes.forEach((node) => {
    const name = node.name || node.id;
    if (!name || graph.hasNode(name)) return;

    const centrality = node.centrality || 0;
    const frequency = node.frequency || 1;
    const baseSize = Math.max(centrality * 120, Math.log2(frequency + 1) * 2.5, 3);
    const size = Math.min(Math.max(baseSize, 3), 22);

    graph.addNode(name, {
      label: name,
      size,
      color: resolveNodeColor(node),
      x: baseX + (Math.random() - 0.5) * spread,
      y: baseY + (Math.random() - 0.5) * spread,
      _data: node,
      _isNew: true,     // flag for entrance animation
      _expanded: false, // becomes true once neighbors are fetched
    });
    added.nodes.push(name);
  });

  (apiData.edges || []).forEach((edge) => {
    const src = typeof edge.source === 'object' ? edge.source.name || edge.source.id : edge.source;
    const tgt = typeof edge.target === 'object' ? edge.target.name || edge.target.id : edge.target;

    if (!src || !tgt || src === tgt) return;
    if (!graph.hasNode(src) || !graph.hasNode(tgt)) return;
    if (graph.hasEdge(src, tgt)) return;

    const weight = edge.weight || 1;
    graph.addEdge(src, tgt, {
      weight,
      size: Math.min(Math.log2(weight + 1) * 0.6, 3),
      color: 'rgba(255,255,255,0.08)',
      _type: edge.type || '',
      _description: edge.description || '',  // stored for semantic hover panel
      _isNew: true,
    });
    added.edges.push(`${src}-${tgt}`);
  });

  return added;
}

// ── Main Component ────────────────────────────────────────────────────
// Props:
//   initialData   — seed graph data ({ nodes, edges }) rendered on mount
//   workspaceId   — passed to the neighbors API
//   onNodeSelect  — fires with node info when user clicks (for NodePanel)
//   hiddenClusters — Set of community IDs to hide
//   onNodeCountChange — optional callback(count) when graph size changes
const KnowledgeGraph = ({
  initialData,
  workspaceId,
  onNodeSelect,
  onNodeCountChange,
}) => {
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const layoutRef = useRef(null);
  const graphRef = useRef(null);                    // persistent Graphology graph
  const expandedRef = useRef(new Set());            // nodes whose neighbors have been fetched
  const expansionChildrenRef = useRef(new Map());  // nodeName → [child node names added by that expansion]
  const loadingNodesRef = useRef(new Set());        // nodes currently being fetched
  const [hoveredNode, setHoveredNode] = useState(null);
  const hoveredNodeRef = useRef(null);              // sync ref for reducer closures
  const [fetchingNode, setFetchingNode] = useState(null);
  const [hoverPanel, setHoverPanel] = useState(null); // { x, y, nodeName, nodeDesc, connections[] }
  const mousePositionRef = useRef({ x: 0, y: 0 });   // live cursor position in px
  const hoverTimerRef = useRef(null);                 // debounce timer for panel

  // ── Fetch neighbors and merge into live graph ─────────────────────
  const expandNode = useCallback(async (nodeName) => {
    if (!workspaceId) return;
    if (expandedRef.current.has(nodeName)) return;        // already expanded
    if (loadingNodesRef.current.has(nodeName)) return;    // fetch in flight

    loadingNodesRef.current.add(nodeName);
    setFetchingNode(nodeName);

    // ── Save camera before any async work ────────────────────────────
    const savedCameraState = sigmaRef.current?.getCamera().getState();

    // ── Read pivot position for spawning new nodes nearby ────────────
    const graph = graphRef.current;
    const pivotX = graph?.hasNode(nodeName) ? graph.getNodeAttribute(nodeName, 'x') : 50;
    const pivotY = graph?.hasNode(nodeName) ? graph.getNodeAttribute(nodeName, 'y') : 50;

    try {
      const data = await api.getNeighbors(nodeName, workspaceId);
      if (!graph) return;

      // Pin all existing nodes so the layout burst only moves new arrivals
      graph.forEachNode((n) => graph.setNodeAttribute(n, 'fixed', true));

      // Merge: new nodes spawn tightly around the pivot position
      const { nodes: addedNodes } = mergeIntoGraph(
        graph, data, expandedRef.current, { x: pivotX, y: pivotY }
      );

      // Track which children this expansion introduced
      expansionChildrenRef.current.set(nodeName, addedNodes);

      // Mark pivot as expanded
      expandedRef.current.add(nodeName);
      if (graph.hasNode(nodeName)) {
        graph.setNodeAttribute(nodeName, '_expanded', true);
      }

      if (addedNodes.length > 0) {
        // Brief synchronous pass — only new (unpinned) nodes will be moved
        forceAtlas2.assign(graph, {
          iterations: 80,
          settings: { gravity: 1, scalingRatio: 2, barnesHutOptimize: true, slowDown: 6 },
        });
      }

      // Unpin all nodes so FA2 can continue naturally
      graph.forEachNode((n) => graph.setNodeAttribute(n, 'fixed', false));

      // Restore camera — viewport never moves
      if (savedCameraState && sigmaRef.current) {
        sigmaRef.current.getCamera().setState(savedCameraState);
      }

      if (sigmaRef.current) sigmaRef.current.refresh();

      // Gentle async refinement for a short burst (doesn't reset camera)
      if (addedNodes.length > 0 && layoutRef.current) {
        layoutRef.current.start();
        setTimeout(() => layoutRef.current?.stop(), 2000);
      }

      // Clear _isNew flags after entrance animation, then update count
      setTimeout(() => {
        addedNodes.forEach((n) => {
          if (graph.hasNode(n)) graph.setNodeAttribute(n, '_isNew', false);
        });
        if (sigmaRef.current) sigmaRef.current.refresh();
        if (onNodeCountChange) onNodeCountChange(graph.order);
      }, 900);
    } catch (err) {
      console.error(`Failed to fetch neighbors for "${nodeName}":`, err);
      // Unpin on error too
      graph?.forEachNode((n) => graph.setNodeAttribute(n, 'fixed', false));
    } finally {
      loadingNodesRef.current.delete(nodeName);
      setFetchingNode(null);
    }
  }, [workspaceId, onNodeCountChange]);

  // ── Collapse: remove a node's exclusive children from the graph ──────
  // A child is "exclusive" if it has degree ≤1 in the current graph,
  // meaning its only connection is back to the pivot (no other anchor).
  // Recursively collapses children that were themselves expanded.
  const collapseNode = useCallback((nodeName) => {
    const graph = graphRef.current;
    if (!graph || !graph.hasNode(nodeName)) return;
    if (!expandedRef.current.has(nodeName)) return;

    const children = expansionChildrenRef.current.get(nodeName) || [];

    children.forEach((child) => {
      if (!graph.hasNode(child)) return;

      // Recursively collapse this child first if it was also expanded
      if (expandedRef.current.has(child)) {
        collapseNode(child);
      }

      // Only remove the child if it's now exclusively connected to the pivot
      // (degree <= 1 means it has no other anchor in the visible graph)
      const degree = graph.degree(child);
      if (degree <= 1) {
        graph.dropNode(child);  // also removes all its edges
        expandedRef.current.delete(child);
        expansionChildrenRef.current.delete(child);
      }
    });

    // Reset the pivot itself to unexpanded so it can be re-expanded
    expandedRef.current.delete(nodeName);
    expansionChildrenRef.current.delete(nodeName);
    if (graph.hasNode(nodeName)) {
      graph.setNodeAttribute(nodeName, '_expanded', false);
    }

    if (sigmaRef.current) sigmaRef.current.refresh();
    if (onNodeCountChange) onNodeCountChange(graph.order);
  }, [onNodeCountChange]);


  // ── Bootstrap: initialize graph + Sigma once on mount ────────────
  useEffect(() => {
    if (!containerRef.current) return;

    // Tear down any previous instance (e.g. workspace change)
    if (sigmaRef.current) { sigmaRef.current.kill(); sigmaRef.current = null; }
    if (layoutRef.current) { layoutRef.current.kill(); layoutRef.current = null; }
    containerRef.current.innerHTML = '';
    expandedRef.current = new Set();
    expansionChildrenRef.current = new Map();
    loadingNodesRef.current = new Set();

    // Create a fresh persistent graph
    const graph = new Graph({ multi: false, type: 'undirected' });
    graphRef.current = graph;

    // Seed the graph with initial data
    if (initialData?.nodes?.length) {
      mergeIntoGraph(graph, initialData, expandedRef.current);
    }

    if (graph.order === 0) return;

    // Initial synchronous layout pass
    forceAtlas2.assign(graph, {
      iterations: 120,
      settings: { gravity: 1, scalingRatio: 2, barnesHutOptimize: true, strongGravityMode: true, slowDown: 5 },
    });

    // Build node reducer (closure over ref so it always reads latest hover)
    const nodeReducer = (node, data) => {
      const res = { ...data };
      const hovered = hoveredNodeRef.current;

      // Entrance flash for newly added nodes
      if (data._isNew) {
        res.color = EXPAND_FLASH_COLOR;
        res.size = (data.size || 8) * 1.4;
      }

      // Ring for expanded nodes (subtle highlight)
      if (data._expanded && !data._isNew) {
        res.highlighted = true;
      }

      // Hover dimming
      if (hovered) {
        if (node === hovered || graph.hasEdge(node, hovered) || graph.hasEdge(hovered, node)) {
          res.highlighted = true;
          res._labelBg = true;   // custom drawLabel will render white pill + black text
          res.zIndex = 1;
        } else {
          res.color = data._isNew ? EXPAND_FLASH_COLOR : 'rgba(255,255,255,0.06)';
          res.label = '';
          res.zIndex = 0;
        }
      }

      return res;
    };

    const edgeReducer = (edge, data) => {
      const res = { ...data };
      const hovered = hoveredNodeRef.current;
      if (hovered) {
        const [src, tgt] = graph.extremities(edge);
        if (src === hovered || tgt === hovered) {
          res.color = 'rgba(255,255,255,0.5)';
          res.size = Math.max(data.size || 1, 1.5);
          res.zIndex = 1;
        } else {
          res.color = 'rgba(255,255,255,0.02)';
          res.hidden = true;
        }
      }
      return res;
    };

    // Create Sigma (single instance for this workspace session)
    const renderer = new Sigma(graph, containerRef.current, {
      allowInvalidContainer: true,
      renderEdgeLabels: false,
      labelFont: 'Inter, sans-serif',
      labelSize: 13,
      labelWeight: '600',
      labelColor: { color: '#e2e8f0' },
      labelDensity: 0.8,
      labelGridCellSize: 80,
      labelRenderedSizeThreshold: 3,
      defaultEdgeType: 'line',
      stagePadding: 30,
      minCameraRatio: 0.05,
      maxCameraRatio: 10,
      nodeReducer,
      edgeReducer,
      // ── Custom label renderer: white pill + black text on hover ──
      drawLabel: (context, data, settings) => {
        if (!data.label) return;

        // Isolate from any canvas state left by node rendering
        context.save();
        context.globalAlpha = 1;
        context.globalCompositeOperation = 'source-over';

        const size = settings.labelSize;
        context.font = `${settings.labelWeight} ${size}px ${settings.labelFont}`;
        const x = data.x + data.size + 3;
        const y = data.y;

        if (data._labelBg) {
          const textWidth = context.measureText(data.label).width;
          const pad = 6;
          const bgX = x - pad;
          const bgY = y - size * 0.75;
          const bgW = textWidth + pad * 2;
          const bgH = size * 1.5;
          const r = 5;

          // White pill background
          context.beginPath();
          context.moveTo(bgX + r, bgY);
          context.lineTo(bgX + bgW - r, bgY);
          context.arcTo(bgX + bgW, bgY, bgX + bgW, bgY + r, r);
          context.lineTo(bgX + bgW, bgY + bgH - r);
          context.arcTo(bgX + bgW, bgY + bgH, bgX + bgW - r, bgY + bgH, r);
          context.lineTo(bgX + r, bgY + bgH);
          context.arcTo(bgX, bgY + bgH, bgX, bgY + bgH - r, r);
          context.lineTo(bgX, bgY + r);
          context.arcTo(bgX, bgY, bgX + r, bgY, r);
          context.closePath();
          context.fillStyle = '#ffffff';
          context.fill();

          // Pure black text on the white pill
          context.fillStyle = '#000000';
          context.fillText(data.label, x, y + size / 3);
        } else {
          // Default non-hovered label: light text, no background
          context.fillStyle = '#e2e8f0';
          context.fillText(data.label, x, y + size / 3);
        }

        context.restore();
      },

    });
    sigmaRef.current = renderer;

    // Start async FA2 for refinement
    const fa2 = new FA2Layout(graph, {
      settings: { gravity: 0.8, scalingRatio: 3, barnesHutOptimize: true, strongGravityMode: true, slowDown: 8 },
    });
    fa2.start();
    layoutRef.current = fa2;
    setTimeout(() => layoutRef.current?.stop(), 4000);

    // ── Events ──────────────────────────────────────────────────────
    renderer.on('clickNode', ({ node }) => {
      const nodeData = graph.getNodeAttributes(node);

      // Fire selection upward for NodePanel
      if (onNodeSelect) {
        onNodeSelect({ name: node, id: nodeData._data?.id || node, ...nodeData._data });
      }

      // Toggle: expand if not yet expanded, collapse if already expanded
      if (expandedRef.current.has(node)) {
        collapseNode(node);
      } else {
        expandNode(node);
      }
    });

    renderer.on('enterNode', ({ node }) => {
      hoveredNodeRef.current = node;
      setHoveredNode(node);
      containerRef.current.style.cursor = 'pointer';
      renderer.refresh();

      // Debounce: show semantic panel after 300ms of stable hover
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = setTimeout(() => {
        const nodeAttrs = graph.getNodeAttributes(node);
        const connections = [];

        graph.forEachEdge(node, (edge, attrs, source, target) => {
          const neighbor = source === node ? target : source;
          const relType = (attrs._type || 'CO_OCCURS')
            .replace(/_/g, ' ')
            .toLowerCase();
          connections.push({
            neighbor,
            type: relType,
            description: attrs._description || '',
          });
        });

        const { x, y } = mousePositionRef.current;
        setHoverPanel({
          x, y,
          nodeName: node,
          nodeDesc: nodeAttrs._data?.description || '',
          connections,
        });
      }, 300);
    });

    renderer.on('leaveNode', () => {
      clearTimeout(hoverTimerRef.current);
      hoveredNodeRef.current = null;
      setHoveredNode(null);
      setHoverPanel(null);
      containerRef.current.style.cursor = 'default';
      renderer.refresh();
    });

    // Initial camera fit
    setTimeout(() => renderer.getCamera().animate({ x: 0.5, y: 0.5, ratio: 1.2 }, { duration: 600 }), 400);

    if (onNodeCountChange) onNodeCountChange(graph.order);

    return () => {
      if (layoutRef.current) { layoutRef.current.kill(); layoutRef.current = null; }
      if (sigmaRef.current) { sigmaRef.current.kill(); sigmaRef.current = null; }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialData, workspaceId]);

  // ── Keep hover reducers live without re-initializing Sigma ─────────
  useEffect(() => {
    const renderer = sigmaRef.current;
    const graph = graphRef.current;
    if (!renderer || !graph) return;

    renderer.setSetting('nodeReducer', (node, data) => {
      const res = { ...data };
      if (data._isNew) { res.color = EXPAND_FLASH_COLOR; res.size = (data.size || 8) * 1.4; }
      if (data._expanded && !data._isNew) res.highlighted = true;
      if (hoveredNode) {
        if (node === hoveredNode || graph.hasEdge(node, hoveredNode) || graph.hasEdge(hoveredNode, node)) {
          res.highlighted = true; res._labelBg = true; res.zIndex = 1;
        } else {
          res.color = data._isNew ? EXPAND_FLASH_COLOR : 'rgba(255,255,255,0.06)';
          res.label = ''; res.zIndex = 0;
        }
      }
      return res;
    });

    renderer.setSetting('edgeReducer', (edge, data) => {
      const res = { ...data };
      if (hoveredNode) {
        const [src, tgt] = graph.extremities(edge);
        if (src === hoveredNode || tgt === hoveredNode) {
          res.color = 'rgba(255,255,255,0.5)'; res.size = Math.max(data.size || 1, 1.5); res.zIndex = 1;
        } else { res.color = 'rgba(255,255,255,0.02)'; res.hidden = true; }
      }
      return res;
    });

    renderer.refresh();
  }, [hoveredNode]);

  // ── Empty state ───────────────────────────────────────────────────
  if (!initialData?.nodes?.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-secondary)' }}>
        No graph data available. Upload a document or paste text to generate a Knowledge Graph.
      </div>
    );
  }

  return (
    <>
      {/* Fetching indicator */}
      {fetchingNode && (
        <div style={{
          position: 'absolute', bottom: '24px', left: '50%', transform: 'translateX(-50%)',
          zIndex: 20, padding: '8px 18px',
          background: 'rgba(136,211,206,0.12)', border: '1px solid rgba(136,211,206,0.35)',
          borderRadius: '20px', fontSize: '0.8rem', color: '#88d3ce',
          display: 'flex', alignItems: 'center', gap: '8px',
          backdropFilter: 'blur(8px)',
          animation: 'fadeIn 0.2s ease',
        }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#88d3ce', animation: 'pulse 1s ease-in-out infinite' }} />
          Expanding <strong>{fetchingNode}</strong>…
        </div>
      )}

      {/* Hint overlay — shows only when the graph has very few nodes */}
      {graphRef.current && graphRef.current.order <= 5 && !fetchingNode && (
        <div style={{
          position: 'absolute', bottom: '24px', right: '24px', zIndex: 15,
          padding: '8px 14px', background: 'rgba(0,0,0,0.4)',
          border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px',
          fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)',
          backdropFilter: 'blur(6px)', pointerEvents: 'none',
        }}>
          Click any node to expand its connections
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translate(-50%, 6px); }
          to   { opacity: 1; transform: translate(-50%, 0); }
        }
        @keyframes panelSlideIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Semantic Hover Panel */}
      {hoverPanel && (
        <div
          onMouseEnter={() => clearTimeout(hoverTimerRef.current)}
          onMouseLeave={() => setHoverPanel(null)}
          style={{
            position: 'absolute',
            left: Math.min(hoverPanel.x + 16, window.innerWidth - 340),
            top: Math.min(hoverPanel.y - 10, window.innerHeight - 300),
            zIndex: 50,
            width: '310px',
            maxHeight: '320px',
            overflowY: 'auto',
            background: 'rgba(10, 12, 22, 0.92)',
            border: '1px solid rgba(136, 211, 206, 0.25)',
            borderRadius: '14px',
            padding: '16px',
            backdropFilter: 'blur(16px)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            animation: 'panelSlideIn 0.2s ease',
            pointerEvents: 'auto',
          }}
        >
          {/* Node name */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: '#88d3ce', flexShrink: 0,
            }} />
            <span style={{ fontWeight: '700', fontSize: '0.95rem', color: '#e2e8f0', letterSpacing: '0.02em' }}>
              {hoverPanel.nodeName}
            </span>
          </div>

          {/* Node description if available */}
          {hoverPanel.nodeDesc && (
            <p style={{
              fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)',
              marginBottom: '12px', lineHeight: '1.5', fontStyle: 'italic',
            }}>
              {hoverPanel.nodeDesc}
            </p>
          )}

          {/* Connection divider */}
          {hoverPanel.connections.length > 0 && (
            <div style={{
              fontSize: '0.68rem', color: '#88d3ce', fontWeight: '600',
              textTransform: 'uppercase', letterSpacing: '0.1em',
              marginBottom: '8px', opacity: 0.8,
            }}>
              Connections ({hoverPanel.connections.length})
            </div>
          )}

          {/* Connection list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {hoverPanel.connections.slice(0, 6).map((conn, i) => (
              <div key={i} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '8px', padding: '9px 11px',
              }}>
                <div style={{ fontSize: '0.78rem', color: '#e2e8f0', lineHeight: '1.55' }}>
                  <span style={{ color: '#88d3ce', fontWeight: '600' }}>
                    {hoverPanel.nodeName}
                  </span>
                  {' is '}
                  <span style={{ color: 'rgba(255,255,255,0.5)', fontStyle: 'italic' }}>
                    {conn.type}
                  </span>
                  {' to '}
                  <span style={{ color: '#FFD166', fontWeight: '600' }}>
                    {conn.neighbor}
                  </span>
                  {conn.description && (
                    <span style={{ color: 'rgba(255,255,255,0.55)' }}>
                      {' — '}{conn.description}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {hoverPanel.connections.length > 6 && (
              <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)', textAlign: 'center', paddingTop: '2px' }}>
                +{hoverPanel.connections.length - 6} more connections
              </div>
            )}
            {hoverPanel.connections.length === 0 && (
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', fontStyle: 'italic' }}>
                No connections visible yet. Click to expand.
              </div>
            )}
          </div>
        </div>
      )}

      <div
        ref={containerRef}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          mousePositionRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        }}
        style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, background: 'transparent' }}
      />
    </>
  );
};

export default KnowledgeGraph;
