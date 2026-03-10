import React, { useEffect, useCallback, useState } from 'react';
import { useFileStore } from '../../store/fileStore';
import { useFolderStore } from '../../store/folderStore';
import { CloudFile } from '../../api/filesApi';
import { formatFileSize, getFileIcon, formatRelativeTime } from '../../utils/fileHelpers';

interface FileBrowserProps {
  folderId?: string | null;
  onFileSelect?: (file: CloudFile) => void;
  onFileOpen?: (file: CloudFile) => void;
}

const FileBrowser: React.FC<FileBrowserProps> = ({
  folderId = null,
  onFileSelect,
  onFileOpen,
}) => {
  const {
    files, isLoading, viewMode, selectedFiles, sortField, sortDirection,
    fetchFiles, toggleStar, deleteFile, toggleFileSelection,
    selectAllFiles, clearSelection, setSorting, setViewMode,
  } = useFileStore();

  const { folders, currentFolder, breadcrumb, fetchFolders, navigateToFolder } =
    useFolderStore();

  const [contextMenu, setContextMenu] = useState<{
    x: number; y: number; file: CloudFile;
  } | null>(null);

  useEffect(() => {
    if (folderId) {
      fetchFiles({ folder: folderId });
      navigateToFolder(folderId);
    } else {
      fetchFiles({ root: true });
      fetchFolders({ root: true });
    }
  }, [folderId, fetchFiles, fetchFolders, navigateToFolder]);

  const handleSort = useCallback((field: string) => {
    const newDirection = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSorting(field, newDirection);
    fetchFiles({ folder: folderId || undefined, root: !folderId });
  }, [sortField, sortDirection, setSorting, fetchFiles, folderId]);

  const handleContextMenu = useCallback((e: React.MouseEvent, file: CloudFile) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, file });
  }, []);

  const handleFileDoubleClick = useCallback((file: CloudFile) => {
    if (onFileOpen) onFileOpen(file);
  }, [onFileOpen]);

  const renderBreadcrumb = () => (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
      <button
        onClick={() => navigateToFolder(null)}
        className="hover:text-blue-600 font-medium"
      >
        My Files
      </button>
      {breadcrumb.map((item, index) => (
        <React.Fragment key={item.id}>
          <span className="text-gray-400">/</span>
          <button
            onClick={() => navigateToFolder(item.id)}
            className={`hover:text-blue-600 ${
              index === breadcrumb.length - 1 ? 'text-gray-900 font-semibold' : ''
            }`}
          >
            {item.name}
          </button>
        </React.Fragment>
      ))}
    </nav>
  );

  const renderToolbar = () => (
    <div className="flex items-center justify-between mb-4 px-2">
      <div className="flex items-center space-x-2">
        {selectedFiles.size > 0 && (
          <>
            <span className="text-sm text-gray-600">
              {selectedFiles.size} selected
            </span>
            <button
              onClick={clearSelection}
              className="text-sm text-blue-600 hover:underline"
            >
              Clear
            </button>
            <button
              onClick={selectAllFiles}
              className="text-sm text-blue-600 hover:underline"
            >
              Select All
            </button>
          </>
        )}
      </div>
      <div className="flex items-center space-x-3">
        <select
          value={`${sortField}:${sortDirection}`}
          onChange={(e) => {
            const [field, dir] = e.target.value.split(':');
            handleSort(field);
          }}
          className="text-sm border rounded px-2 py-1"
        >
          <option value="updated_at:desc">Last Modified</option>
          <option value="name:asc">Name (A-Z)</option>
          <option value="name:desc">Name (Z-A)</option>
          <option value="size:desc">Size (Largest)</option>
          <option value="size:asc">Size (Smallest)</option>
          <option value="created_at:desc">Date Created</option>
        </select>
        <div className="flex border rounded overflow-hidden">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 text-sm ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 text-sm ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
          >
            List
          </button>
        </div>
      </div>
    </div>
  );

  const renderGridView = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {folders.map((folder) => (
        <div
          key={folder.id}
          onDoubleClick={() => navigateToFolder(folder.id)}
          className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md cursor-pointer transition-all"
        >
          <div className="w-12 h-12 mb-2 flex items-center justify-center">
            <svg className="w-10 h-10" fill={folder.color} viewBox="0 0 24 24">
              <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
            </svg>
          </div>
          <span className="text-sm font-medium text-gray-800 text-center truncate w-full">
            {folder.name}
          </span>
          <span className="text-xs text-gray-500">{folder.file_count} files</span>
        </div>
      ))}

      {files.map((file) => (
        <div
          key={file.id}
          onClick={() => { onFileSelect?.(file); toggleFileSelection(file.id); }}
          onDoubleClick={() => handleFileDoubleClick(file)}
          onContextMenu={(e) => handleContextMenu(e, file)}
          className={`flex flex-col items-center p-4 rounded-lg border cursor-pointer transition-all ${
            selectedFiles.has(file.id)
              ? 'border-blue-500 bg-blue-50 shadow-md'
              : 'border-gray-200 hover:border-blue-300 hover:shadow-sm'
          }`}
        >
          <div className="w-12 h-12 mb-2 flex items-center justify-center text-2xl">
            {getFileIcon(file.file_type_category)}
          </div>
          <span className="text-sm font-medium text-gray-800 text-center truncate w-full">
            {file.name}
          </span>
          <span className="text-xs text-gray-500">{file.size_display}</span>
        </div>
      ))}
    </div>
  );

  const renderListView = () => (
    <table className="w-full text-sm">
      <thead className="bg-gray-50 border-b">
        <tr>
          <th className="text-left px-4 py-3 font-medium text-gray-600">
            <input
              type="checkbox"
              checked={selectedFiles.size === files.length && files.length > 0}
              onChange={() =>
                selectedFiles.size === files.length ? clearSelection() : selectAllFiles()
              }
              className="rounded"
            />
          </th>
          <th
            className="text-left px-4 py-3 font-medium text-gray-600 cursor-pointer hover:text-gray-900"
            onClick={() => handleSort('name')}
          >
            Name {sortField === 'name' && (sortDirection === 'asc' ? ' ^' : ' v')}
          </th>
          <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
          <th
            className="text-left px-4 py-3 font-medium text-gray-600 cursor-pointer hover:text-gray-900"
            onClick={() => handleSort('size')}
          >
            Size {sortField === 'size' && (sortDirection === 'asc' ? ' ^' : ' v')}
          </th>
          <th
            className="text-left px-4 py-3 font-medium text-gray-600 cursor-pointer hover:text-gray-900"
            onClick={() => handleSort('updated_at')}
          >
            Modified {sortField === 'updated_at' && (sortDirection === 'asc' ? ' ^' : ' v')}
          </th>
          <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
        </tr>
      </thead>
      <tbody>
        {folders.map((folder) => (
          <tr
            key={folder.id}
            onDoubleClick={() => navigateToFolder(folder.id)}
            className="border-b hover:bg-gray-50 cursor-pointer"
          >
            <td className="px-4 py-3"></td>
            <td className="px-4 py-3 flex items-center space-x-3">
              <svg className="w-5 h-5" fill={folder.color} viewBox="0 0 24 24">
                <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
              </svg>
              <span className="font-medium">{folder.name}</span>
            </td>
            <td className="px-4 py-3 text-gray-500">Folder</td>
            <td className="px-4 py-3 text-gray-500">{folder.file_count} items</td>
            <td className="px-4 py-3 text-gray-500">{formatRelativeTime(folder.updated_at)}</td>
            <td className="px-4 py-3 text-right">-</td>
          </tr>
        ))}
        {files.map((file) => (
          <tr
            key={file.id}
            onClick={() => toggleFileSelection(file.id)}
            onDoubleClick={() => handleFileDoubleClick(file)}
            onContextMenu={(e) => handleContextMenu(e, file)}
            className={`border-b cursor-pointer ${
              selectedFiles.has(file.id) ? 'bg-blue-50' : 'hover:bg-gray-50'
            }`}
          >
            <td className="px-4 py-3">
              <input
                type="checkbox"
                checked={selectedFiles.has(file.id)}
                onChange={() => toggleFileSelection(file.id)}
                className="rounded"
              />
            </td>
            <td className="px-4 py-3 flex items-center space-x-3">
              <span className="text-lg">{getFileIcon(file.file_type_category)}</span>
              <span className="font-medium">{file.name}</span>
              {file.is_starred && <span className="text-yellow-500 text-xs">*</span>}
            </td>
            <td className="px-4 py-3 text-gray-500 capitalize">{file.file_type_category}</td>
            <td className="px-4 py-3 text-gray-500">{file.size_display}</td>
            <td className="px-4 py-3 text-gray-500">{formatRelativeTime(file.updated_at)}</td>
            <td className="px-4 py-3 text-right">
              <button
                onClick={(e) => { e.stopPropagation(); toggleStar(file.id); }}
                className="text-gray-400 hover:text-yellow-500 mr-2"
                title={file.is_starred ? 'Unstar' : 'Star'}
              >
                {file.is_starred ? '*' : '-'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  if (isLoading && files.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {renderBreadcrumb()}
      {renderToolbar()}
      {files.length === 0 && folders.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <p className="text-lg font-medium">This folder is empty</p>
          <p className="text-sm">Upload files or create folders to get started</p>
        </div>
      ) : viewMode === 'grid' ? (
        renderGridView()
      ) : (
        renderListView()
      )}

      {contextMenu && (
        <div
          className="fixed bg-white rounded-lg shadow-xl border py-1 z-50 min-w-48"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onMouseLeave={() => setContextMenu(null)}
        >
          <button className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm" onClick={() => { onFileOpen?.(contextMenu.file); setContextMenu(null); }}>
            Open
          </button>
          <button className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm" onClick={() => { toggleStar(contextMenu.file.id); setContextMenu(null); }}>
            {contextMenu.file.is_starred ? 'Remove Star' : 'Add Star'}
          </button>
          <hr className="my-1" />
          <button className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-red-600" onClick={() => { deleteFile(contextMenu.file.id); setContextMenu(null); }}>
            Move to Trash
          </button>
        </div>
      )}
    </div>
  );
};

export default FileBrowser;
