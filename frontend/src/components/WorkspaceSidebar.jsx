import React, { useState } from 'react';
import { FolderOpen, Plus, Trash2, ChevronLeft, ChevronRight, Check, X } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';

const WorkspaceSidebar = ({ collapsed, onToggle }) => {
  const { workspaces, activeWorkspace, setActiveWorkspace, createWorkspace, deleteWorkspace, renameWorkspace } = useWorkspace();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await createWorkspace(newName.trim());
    setNewName(''); setCreating(false);
  };

  const startRename = (ws, e) => {
    e.stopPropagation();
    setRenamingId(ws.id); setRenameValue(ws.name);
  };

  const commitRename = async () => {
    if (renameValue.trim()) await renameWorkspace(renamingId, renameValue.trim());
    setRenamingId(null);
  };

  const handleDelete = async (ws, e) => {
    e.stopPropagation();
    if (deletingId === ws.id) { await deleteWorkspace(ws.id); setDeletingId(null); }
    else setDeletingId(ws.id);
  };

  return (
    <div style={{
      width: collapsed ? '52px' : '240px', minHeight: '100vh',
      background: 'rgba(10, 10, 26, 0.85)', borderRight: '1px solid rgba(255,255,255,0.06)',
      backdropFilter: 'blur(12px)', transition: 'width 0.25s ease',
      display: 'flex', flexDirection: 'column', overflow: 'hidden', flexShrink: 0,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)', minHeight: '56px',
      }}>
        {!collapsed && (
          <span style={{ fontWeight: 700, fontSize: '0.8rem', letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            Workspaces
          </span>
        )}
        <button onClick={onToggle} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px', marginLeft: 'auto' }}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {workspaces.map(ws => {
          const isActive = ws.id === activeWorkspace?.id;
          const isRenaming = renamingId === ws.id;
          const isDeleting = deletingId === ws.id;
          return (
            <div key={ws.id}
              onClick={() => { if (!isRenaming) { setActiveWorkspace(ws); setDeletingId(null); }}}
              onDoubleClick={(e) => startRename(ws, e)}
              title={collapsed ? ws.name : undefined}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: collapsed ? '12px' : '10px 12px', margin: '2px 6px',
                borderRadius: '8px', cursor: 'pointer',
                background: isActive ? 'rgba(136, 211, 206, 0.12)' : isDeleting ? 'rgba(255,107,107,0.1)' : 'transparent',
                border: `1px solid ${isActive ? 'rgba(136,211,206,0.3)' : 'transparent'}`,
                transition: 'all 0.15s ease', justifyContent: collapsed ? 'center' : 'flex-start',
              }}
            >
              <FolderOpen size={16} color={isActive ? '#88d3ce' : 'var(--text-secondary)'} style={{ flexShrink: 0 }} />
              {!collapsed && (isRenaming ? (
                <input autoFocus value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onBlur={commitRename}
                  onKeyDown={e => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenamingId(null); }}
                  onClick={e => e.stopPropagation()}
                  style={{ flex: 1, background: 'rgba(255,255,255,0.08)', border: '1px solid var(--accent-color)', borderRadius: '4px', color: '#fff', fontSize: '0.85rem', padding: '2px 6px', outline: 'none' }}
                />
              ) : (
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: isActive ? 600 : 400, color: isActive ? '#fff' : 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {ws.name}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)' }}>
                    {ws.document_count ?? 0} doc{ws.document_count !== 1 ? 's' : ''}
                  </div>
                </div>
              ))}
              {!collapsed && !isRenaming && (
                <button onClick={(e) => handleDelete(ws, e)}
                  title={isDeleting ? 'Click again to confirm' : 'Delete'}
                  style={{ background: 'none', border: 'none', color: isDeleting ? '#FF6B6B' : 'rgba(255,255,255,0.2)', cursor: 'pointer', padding: '2px', borderRadius: '4px', flexShrink: 0, transition: 'color 0.2s' }}>
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Create */}
      {!collapsed && (
        <div style={{ padding: '8px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          {creating ? (
            <div style={{ display: 'flex', gap: '6px' }}>
              <input autoFocus value={newName} onChange={e => setNewName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleCreate(); if (e.key === 'Escape') { setCreating(false); setNewName(''); }}}
                placeholder="Workspace name…"
                style={{ flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '6px', color: '#fff', fontSize: '0.82rem', padding: '7px 10px', outline: 'none' }}
              />
              <button onClick={handleCreate} style={{ background: 'rgba(136,211,206,0.15)', border: '1px solid rgba(136,211,206,0.3)', borderRadius: '6px', color: '#88d3ce', cursor: 'pointer', padding: '0 8px' }}><Check size={14} /></button>
              <button onClick={() => { setCreating(false); setNewName(''); }} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0 8px' }}><X size={14} /></button>
            </div>
          ) : (
            <button onClick={() => setCreating(true)} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px', background: 'rgba(255,255,255,0.04)', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '7px', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.82rem', transition: 'all 0.2s' }}>
              <Plus size={14} /> New Workspace
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkspaceSidebar;
