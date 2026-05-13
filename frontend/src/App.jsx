import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import GraphExplorer from './pages/GraphExplorer';
import Research from './pages/Research';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/research" element={<Research />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
