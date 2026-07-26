/**
 * NotificationContext
 * Global toast notification system.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
}

interface NotificationContextType {
  toasts: ToastItem[];
  addToast: (type: NotificationType, title: string, message: string) => void;
  removeToast: (id: string) => void;
}

const NotificationContext = createContext<NotificationContextType>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
});

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((type: NotificationType, title: string, message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      removeToast(id);
    }, 4000);
  }, [removeToast]);

  return (
    <NotificationContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => useContext(NotificationContext);
