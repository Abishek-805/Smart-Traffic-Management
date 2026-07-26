/**
 * useKeyboardNav Hook (src/shared/hooks/useKeyboardNav.ts)
 * Arrow-key navigation across a list of string keys (e.g. NSEW directions).
 * Returns a ref-callback and the currently focused key.
 * WCAG AA: enables keyboard operability for LaneCard grid navigation.
 */

import { useCallback, useRef, useState } from 'react';

export interface UseKeyboardNavOptions {
  items: string[];
  initialIndex?: number;
  onSelect?: (item: string) => void;
  loop?: boolean;
}

export interface UseKeyboardNavResult {
  focusedKey: string;
  getItemProps: (key: string) => {
    tabIndex: number;
    'aria-selected': boolean;
    onKeyDown: (e: React.KeyboardEvent) => void;
    onFocus: () => void;
    ref: (el: HTMLElement | null) => void;
  };
}

export const useKeyboardNav = ({
  items,
  initialIndex = 0,
  onSelect,
  loop = true,
}: UseKeyboardNavOptions): UseKeyboardNavResult => {
  const [focusedIndex, setFocusedIndex] = useState<number>(initialIndex);
  const elementRefs = useRef<Map<string, HTMLElement | null>>(new Map());

  const focusItem = useCallback(
    (index: number) => {
      const clampedIndex = loop
        ? ((index % items.length) + items.length) % items.length
        : Math.max(0, Math.min(index, items.length - 1));
      setFocusedIndex(clampedIndex);
      const key = items[clampedIndex];
      elementRefs.current.get(key)?.focus();
    },
    [items, loop],
  );

  const getItemProps = useCallback(
    (key: string) => {
      const index = items.indexOf(key);
      return {
        tabIndex: index === focusedIndex ? 0 : -1,
        'aria-selected': index === focusedIndex,
        onFocus: () => setFocusedIndex(index),
        ref: (el: HTMLElement | null) => {
          elementRefs.current.set(key, el);
        },
        onKeyDown: (e: React.KeyboardEvent) => {
          switch (e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
              e.preventDefault();
              focusItem(index + 1);
              break;
            case 'ArrowLeft':
            case 'ArrowUp':
              e.preventDefault();
              focusItem(index - 1);
              break;
            case 'Enter':
            case ' ':
              e.preventDefault();
              onSelect?.(key);
              break;
            default:
              break;
          }
        },
      };
    },
    [focusedIndex, focusItem, items, onSelect],
  );

  return {
    focusedKey: items[focusedIndex],
    getItemProps,
  };
};
