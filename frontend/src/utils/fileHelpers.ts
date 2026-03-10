/**
 * Format a file size in bytes to a human-readable string.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const base = 1024;
  const unitIndex = Math.floor(Math.log(bytes) / Math.log(base));
  const size = bytes / Math.pow(base, unitIndex);

  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

/**
 * Format an ISO date string to a relative time string (e.g., "2 hours ago").
 */
export function formatRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) return 'just now';
  if (diffSeconds < 3600) {
    const minutes = Math.floor(diffSeconds / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  }
  if (diffSeconds < 86400) {
    const hours = Math.floor(diffSeconds / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }
  if (diffSeconds < 604800) {
    const days = Math.floor(diffSeconds / 86400);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  }
  if (diffSeconds < 2592000) {
    const weeks = Math.floor(diffSeconds / 604800);
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

/**
 * Get a display icon/label for a file type category.
 */
export function getFileIcon(category: string): string {
  const icons: Record<string, string> = {
    image: '[IMG]',
    pdf: '[PDF]',
    text: '[TXT]',
    audio: '[AUD]',
    video: '[VID]',
    document: '[DOC]',
    archive: '[ZIP]',
    other: '[FILE]',
  };
  return icons[category] || icons.other;
}

/**
 * Get the MIME type category for display purposes.
 */
export function getMimeCategory(mimeType: string): string {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('audio/')) return 'audio';
  if (mimeType.startsWith('text/')) return 'text';
  if (mimeType === 'application/pdf') return 'pdf';
  if (mimeType.includes('word') || mimeType.includes('document')) return 'document';
  if (mimeType.includes('sheet') || mimeType.includes('excel')) return 'spreadsheet';
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return 'presentation';
  if (mimeType.includes('zip') || mimeType.includes('compressed') || mimeType.includes('tar') || mimeType.includes('gzip')) return 'archive';
  return 'other';
}

/**
 * Extract file extension from a filename.
 */
export function getFileExtension(filename: string): string {
  const lastDot = filename.lastIndexOf('.');
  if (lastDot === -1 || lastDot === 0) return '';
  return filename.substring(lastDot + 1).toLowerCase();
}

/**
 * Generate a safe filename by removing/replacing invalid characters.
 */
export function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
    .replace(/^\.+/, '')
    .replace(/\.+$/, '')
    .trim();
}

/**
 * Check if a file can be previewed in the browser.
 */
export function isPreviewable(mimeType: string): boolean {
  const previewable = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
    'application/pdf',
    'text/plain', 'text/html', 'text/css', 'text/javascript', 'text/csv',
    'application/json', 'text/markdown',
    'audio/mpeg', 'audio/wav', 'audio/ogg',
    'video/mp4', 'video/webm',
  ];
  return previewable.includes(mimeType);
}

/**
 * Get a color for a file type category, used in UI elements.
 */
export function getFileCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    image: '#3B82F6',
    pdf: '#EF4444',
    text: '#6B7280',
    audio: '#8B5CF6',
    video: '#EC4899',
    document: '#2563EB',
    archive: '#F59E0B',
    other: '#9CA3AF',
  };
  return colors[category] || colors.other;
}

/**
 * Sort files by a given field and direction.
 */
export function sortFiles<T extends Record<string, any>>(
  files: T[],
  field: string,
  direction: 'asc' | 'desc' = 'asc'
): T[] {
  return [...files].sort((a, b) => {
    let valA = a[field];
    let valB = b[field];

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return direction === 'asc' ? -1 : 1;
    if (valA > valB) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Calculate total size of an array of files.
 */
export function calculateTotalSize(files: Array<{ size: number }>): number {
  return files.reduce((total, file) => total + file.size, 0);
}
