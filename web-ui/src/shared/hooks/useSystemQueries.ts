/**
 * Custom React Query Hooks for cached server state and API mutations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemApi } from '../../services/api/system';
import { cameraApi } from '../../services/api/camera';
import { nodeApi } from '../../services/api/node';
import { analyticsApi } from '../../services/api/analytics';
import { logsApi } from '../../services/api/logs';
import { LogCategory } from '../../types';

export function useSystemHealth() {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: systemApi.getHealth,
    refetchInterval: 5000,
  });
}

export function useVersionInfo() {
  return useQuery({
    queryKey: ['versionInfo'],
    queryFn: systemApi.getVersion,
    staleTime: Infinity,
  });
}

export function useCameraConfigs() {
  return useQuery({
    queryKey: ['cameraConfigs'],
    queryFn: cameraApi.getCameras,
    refetchInterval: 10000,
  });
}

export function useMobileNodes() {
  return useQuery({
    queryKey: ['mobileNodes'],
    queryFn: nodeApi.getMobileNodes,
    refetchInterval: 5000,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: analyticsApi.getAnalyticsSummary,
    refetchInterval: 15000,
  });
}

export function useLogs(category: LogCategory = 'ALL', level: string = 'ALL', search?: string) {
  return useQuery({
    queryKey: ['logs', category, level, search],
    queryFn: () => logsApi.getLogs(category, level, search),
    refetchInterval: 3000,
  });
}

export function useSystemControls() {
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: systemApi.startSystem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['systemHealth'] }),
  });

  const stopMutation = useMutation({
    mutationFn: systemApi.stopSystem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['systemHealth'] }),
  });

  const restartMutation = useMutation({
    mutationFn: systemApi.restartSystem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['systemHealth'] }),
  });

  return { startMutation, stopMutation, restartMutation };
}
