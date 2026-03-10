import { useState, useCallback, useRef, useEffect } from 'react';
import apiClient from '../api/client';
import { CloudFile } from '../api/filesApi';
import { Folder } from '../api/foldersApi';

interface SearchResult {
  query: string;
  files: CloudFile[];
  folders: Folder[];
  total_count: number;
}

interface SearchSuggestion {
  text: string;
  type: 'file' | 'folder' | 'extension';
}

/**
 * Hook for global search functionality with debounced suggestions
 * and full search results.
 */
export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSuggestLoading, setIsSuggestLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const fetchSuggestions = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    setIsSuggestLoading(true);
    try {
      const response = await apiClient.get('/search/suggestions/', {
        params: { q: searchQuery },
      });
      setSuggestions(response.data.suggestions || []);
    } catch {
      setSuggestions([]);
    } finally {
      setIsSuggestLoading(false);
    }
  }, []);

  const updateQuery = useCallback(
    (newQuery: string) => {
      setQuery(newQuery);

      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        fetchSuggestions(newQuery);
      }, 300);
    },
    [fetchSuggestions]
  );

  const performSearch = useCallback(
    async (searchQuery?: string, type: string = 'all') => {
      const q = searchQuery || query;
      if (q.length < 2) {
        setSearchError('Search query must be at least 2 characters');
        return;
      }

      setIsSearching(true);
      setSearchError(null);
      setSuggestions([]);

      try {
        const response = await apiClient.get('/search/', {
          params: { q, type },
        });
        setResults(response.data);
      } catch (err: any) {
        setSearchError(
          err.response?.data?.error || 'Search failed. Please try again.'
        );
        setResults(null);
      } finally {
        setIsSearching(false);
      }
    },
    [query]
  );

  const performAdvancedSearch = useCallback(
    async (params: {
      query?: string;
      file_types?: string[];
      min_size?: number;
      max_size?: number;
      date_from?: string;
      date_to?: string;
      folder_id?: string;
      starred_only?: boolean;
      sort_by?: string;
    }) => {
      setIsSearching(true);
      setSearchError(null);

      try {
        const response = await apiClient.post('/search/advanced/', params);
        setResults({
          query: params.query || '',
          files: response.data.results || [],
          folders: [],
          total_count: response.data.count || 0,
        });
      } catch (err: any) {
        setSearchError(
          err.response?.data?.error || 'Search failed. Please try again.'
        );
        setResults(null);
      } finally {
        setIsSearching(false);
      }
    },
    []
  );

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults(null);
    setSuggestions([]);
    setSearchError(null);
  }, []);

  return {
    query,
    results,
    suggestions,
    isSearching,
    isSuggestLoading,
    searchError,
    updateQuery,
    performSearch,
    performAdvancedSearch,
    clearSearch,
  };
}
