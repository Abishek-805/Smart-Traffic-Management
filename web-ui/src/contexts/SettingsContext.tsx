/**
 * SettingsContext
 * LocalStorage backed application settings state manager.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserSettings } from '../types';

const defaultSettings: UserSettings = {
  theme: 'dark',
  confidenceThreshold: 0.5,
  minGreenTime: 10,
  maxGreenTime: 60,
  comPort: 'COM3',
  baudRate: 115200,
  autoRefreshRate: 5,
  enableNotifications: true,
};

interface SettingsContextType {
  settings: UserSettings;
  updateSettings: (partial: Partial<UserSettings>) => void;
  resetSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType>({
  settings: defaultSettings,
  updateSettings: () => {},
  resetSettings: () => {},
});

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<UserSettings>(() => {
    try {
      const saved = localStorage.getItem('app_user_settings');
      return saved ? JSON.parse(saved) : defaultSettings;
    } catch {
      return defaultSettings;
    }
  });

  useEffect(() => {
    localStorage.setItem('app_user_settings', JSON.stringify(settings));
  }, [settings]);

  const updateSettings = (partial: Partial<UserSettings>) => {
    setSettings((prev) => ({ ...prev, ...partial }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => useContext(SettingsContext);
