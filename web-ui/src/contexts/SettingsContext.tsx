/**
 * SettingsContext
 * LocalStorage backed application settings state manager.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserSettings } from '../types';

const defaultSettings: UserSettings = {
  theme: 'dark',
  confidenceThreshold: 0.08,
  minGreenTime: 10,
  maxGreenTime: 60,
  autoRefreshRate: 5,
  enableNotifications: true,
};

const SETTINGS_VERSION = '2';

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
      if (!saved) return defaultSettings;
      const parsed = { ...defaultSettings, ...JSON.parse(saved) };
      // Version 2 lowers the detector floor so ByteTrack can recover weak,
      // partially occluded vehicles. Migrate the old 0.35 default once.
      if (localStorage.getItem('app_user_settings_version') !== SETTINGS_VERSION) {
        parsed.confidenceThreshold = defaultSettings.confidenceThreshold;
      }
      return parsed;
    } catch {
      return defaultSettings;
    }
  });

  useEffect(() => {
    localStorage.setItem('app_user_settings', JSON.stringify(settings));
    localStorage.setItem('app_user_settings_version', SETTINGS_VERSION);
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
