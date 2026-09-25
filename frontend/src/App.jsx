import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import WorkspaceSidebar from './components/WorkspaceSidebar';
import Dashboard from './pages/Dashboard';
import GraphExplorer from './pages/GraphExplorer';
import Research from './pages/Research';
import { WorkspaceProvider } from './context/WorkspaceContext';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <WorkspaceProvider>
      <BrowserRouter>
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Header />
          <div style={{ display: 'flex', flex: 1 }}>
            <WorkspaceSidebar
              collapsed={sidebarCollapsed}
              onToggle={() => setSidebarCollapsed(p => !p)}
            />
            <main style={{ flex: 1, overflow: 'auto' }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/graph" element={<GraphExplorer />} />
                <Route path="/research" element={<Research />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </WorkspaceProvider>
  );
}

export default App;
