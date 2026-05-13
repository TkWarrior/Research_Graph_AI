import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

// Expanded and vibrant color palette for different entity types
const NODE_COLORS = {
  PERSON: '#FF6B6B',      // Coral Red
  ORGANIZATION: '#4ECDC4', // Turquoise
  CONCEPT: '#FFE66D',      // Bright Yellow
  TECHNOLOGY: '#4D96FF',   // Bright Blue
  LOCATION: '#FF9F1C',     // Orange
  EVENT: '#A29BFE',        // Periwinkle
  METRIC: '#00D2D3',       // Cyan
  DATE: '#F368E0',         // Pink
  PROCESS: '#10AC84',      // Sea Green
  DEFAULT: '#FFFFFF'       // White
};

const KnowledgeGraph = ({ graphData, onNodeClick }) => {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef();
  const [hoverNode, setHoverNode] = useState(null);
  const [hoverLink, setHoverLink] = useState(null);

  // Resize graph on window resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    
    window.addEventListener('resize', updateDimensions);
    updateDimensions();
    setTimeout(updateDimensions, 100);
    
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Zoom to fit graph when data loads
  useEffect(() => {
    if (graphData && graphData.nodes && graphData.nodes.length > 0 && fgRef.current) {
      // Calculate degrees for node sizing
      const degreeMap = {};
      graphData.edges?.forEach(edge => {
        const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
        const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
        degreeMap[sourceId] = (degreeMap[sourceId] || 0) + 1;
        degreeMap[targetId] = (degreeMap[targetId] || 0) + 1;
      });
      
      graphData.nodes.forEach(node => {
        node.val = (degreeMap[node.id] || 0) + 2; // Base size + degree
      });

      // Adjust physics to keep nodes slightly closer together
      fgRef.current.d3Force('charge').strength(-150);
      fgRef.current.d3Force('link').distance(40);

      // Give physics a moment to settle, then zoom to fit all nodes
      setTimeout(() => {
        // padding: 20px means it will zoom in as much as possible while keeping all nodes on screen
        fgRef.current.zoomToFit(800, 20); 
      }, 800);
    }
  }, [graphData]);

  const getNodeColor = useCallback((node) => {
    const type = node.type?.toUpperCase() || 'DEFAULT';
    return NODE_COLORS[type] || NODE_COLORS.DEFAULT;
  }, []);

  // Set up highlighted sets for hover effects
  const { highlightNodes, highlightLinks } = useMemo(() => {
    const nodes = new Set();
    const links = new Set();

    if (hoverNode) {
      nodes.add(hoverNode.id);
      graphData.edges?.forEach(link => {
        if (link.source.id === hoverNode.id || link.target.id === hoverNode.id) {
          links.add(link);
          nodes.add(link.source.id);
          nodes.add(link.target.id);
        }
      });
    }

    if (hoverLink) {
      links.add(hoverLink);
      nodes.add(hoverLink.source.id);
      nodes.add(hoverLink.target.id);
    }

    return { highlightNodes: nodes, highlightLinks: links };
  }, [graphData, hoverNode, hoverLink]);

  const drawNodeCanvas = useCallback((node, ctx, globalScale) => {
    const label = node.name || node.id;
    const isHighlighted = hoverNode ? highlightNodes.has(node.id) : false;
    const isMuted = hoverNode || hoverLink ? !highlightNodes.has(node.id) : false;
    
    // Dynamic node size based on degree (node.val calculated earlier)
    // We significantly increased the multiplier and the max-size cap
    const nodeR = Math.min(Math.max((node.val || 2) * 3, 8), 32); 
    const color = getNodeColor(node);
    
    // Draw glow effect for highlighted nodes
    if (isHighlighted) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 15;
    } else {
      ctx.shadowBlur = 0;
    }

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeR, 0, 2 * Math.PI, false);
    ctx.fillStyle = isMuted ? 'rgba(255,255,255,0.1)' : color;
    ctx.fill();
    
    // Reset shadow
    ctx.shadowBlur = 0;

    // Draw border
    ctx.lineWidth = isHighlighted ? 2 / globalScale : 1 / globalScale;
    ctx.strokeStyle = isMuted ? 'transparent' : '#1A1A2E';
    ctx.stroke();

    // Draw label
    if (!isMuted && (globalScale >= 1.2 || isHighlighted)) {
      const fontSize = isHighlighted ? 14 / globalScale : 11 / globalScale;
      ctx.font = `${isHighlighted ? 'bold ' : ''}${fontSize}px Inter, sans-serif`;
      
      const textWidth = ctx.measureText(label).width;
      const bgDimensions = [textWidth + 8, fontSize + 4];

      // Draw label background
      ctx.fillStyle = 'rgba(10, 10, 26, 0.85)';
      ctx.beginPath();
      ctx.roundRect(node.x - bgDimensions[0] / 2, node.y + nodeR + 4, bgDimensions[0], bgDimensions[1], 4 / globalScale);
      ctx.fill();
      
      // Draw text
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isHighlighted ? '#FFFFFF' : 'rgba(255,255,255,0.8)';
      ctx.fillText(label, node.x, node.y + nodeR + 4 + bgDimensions[1] / 2);
    }
  }, [hoverNode, hoverLink, highlightNodes, getNodeColor]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-secondary)' }}>
        No graph data available. Upload a document to generate a Knowledge Graph.
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={{ nodes: graphData.nodes, links: graphData.edges }}
        
        // Node Rendering
        nodeLabel={() => ''} // Handled by custom canvas
        nodeColor={getNodeColor}
        nodeCanvasObject={drawNodeCanvas}
        nodeCanvasObjectMode={() => 'replace'}
        nodeRelSize={12}
        
        // Link Rendering
        linkColor={(link) => highlightLinks.has(link) ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.15)'}
        linkWidth={(link) => highlightLinks.has(link) ? 3 : 1}
        linkDirectionalArrowLength={(link) => highlightLinks.has(link) ? 6 : 3.5}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.2}
        
        // Link Labels (Hover only)
        linkLabel={(link) => `<div style="background:rgba(0,0,0,0.8);padding:4px 8px;border-radius:4px;font-size:12px;">${link.type}</div>`}
        
        // Link Particles
        linkDirectionalParticles={(link) => highlightLinks.has(link) ? 4 : 0}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleSpeed={0.01}
        
        // Interactions
        onNodeClick={(node) => {
          // Smoothly pan camera to center on the clicked node and zoom in
          fgRef.current.centerAt(node.x, node.y, 800);
          fgRef.current.zoom(2.5, 800);
          onNodeClick(node);
        }}
        onNodeHover={node => setHoverNode(node || null)}
        onLinkHover={link => setHoverLink(link || null)}
        enableNodeDrag={false}
        
        // Physics & Container
        backgroundColor="transparent"
        d3AlphaDecay={0.03}
        d3VelocityDecay={0.2}
      />
    </div>
  );
};

export default KnowledgeGraph;
