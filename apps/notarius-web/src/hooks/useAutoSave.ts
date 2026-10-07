import { useCallback, useEffect, useRef, useState } from 'react';

export interface AutoSaveOptions {
  delay?: number;
  onSave: (data: unknown) => Promise<void>;
  onError?: (error: Error) => void;
  enabled?: boolean;
}

export interface AutoSaveState {
  isSaving: boolean;
  lastSaved: Date | null;
  error: Error | null;
  hasUnsavedChanges: boolean;
}

export function useAutoSave<T>(
  data: T,
  options: AutoSaveOptions
): AutoSaveState {
  const {
    delay = 500,
    onSave,
    onError,
    enabled = true
  } = options;

  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const timeoutRef = useRef<NodeJS.Timeout>();
  const lastSavedDataRef = useRef<T>(data);
  const isInitialMount = useRef(true);

  // Check if data has changed
  const dataChanged = JSON.stringify(data) !== JSON.stringify(lastSavedDataRef.current);

  // Update unsaved changes state
  useEffect(() => {
    if (!isInitialMount.current && dataChanged) {
      setHasUnsavedChanges(true);
    }
    isInitialMount.current = false;
  }, [dataChanged]);

  // Auto-save effect
  useEffect(() => {
    if (!enabled || !dataChanged || isSaving) {
      return;
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    timeoutRef.current = setTimeout(async () => {
      try {
        setIsSaving(true);
        setError(null);
        
        await onSave(data);
        
        lastSavedDataRef.current = data;
        setLastSaved(new Date());
        setHasUnsavedChanges(false);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Erro desconhecido ao salvar');
        setError(error);
        onError?.(error);
      } finally {
        setIsSaving(false);
      }
    }, delay);

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, delay, onSave, onError, enabled, isSaving, dataChanged]);

  // Manual save function
  const saveNow = useCallback(async () => {
    if (isSaving || !enabled) {
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      
      await onSave(data);
      
      lastSavedDataRef.current = data;
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Erro desconhecido ao salvar');
      setError(error);
      onError?.(error);
    } finally {
      setIsSaving(false);
    }
  }, [data, onSave, onError, enabled, isSaving]);

  // Reset error function
  const resetError = useCallback(() => {
    setError(null);
  }, []);

  // Force save (bypass debounce)
  const forceSave = useCallback(async () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    await saveNow();
  }, [saveNow]);

  return {
    isSaving,
    lastSaved,
    error,
    hasUnsavedChanges,
    // Expose additional functions
    saveNow,
    resetError,
    forceSave
  } as AutoSaveState & {
    saveNow: () => Promise<void>;
    resetError: () => void;
    forceSave: () => Promise<void>;
  };
}

