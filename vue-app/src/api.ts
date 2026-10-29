import type {
  EventItem,
  FolderInfo,
  FolderReplay,
  GameDetail,
  GameSummary,
  ImportJob,
  PlayerStat,
  TechTiming,
  UnitLifecycle,
} from './types-analysis'

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) || 'http://127.0.0.1:8765'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${text}`)
  }
  return (await response.json()) as T
}

export const api = {
  base: API_BASE,
  health: () => request<{ status: string; schema: string; migrations: string[] }>('/api/health'),
  folders: () => request<FolderInfo[]>('/api/folders'),
  games: (folderId?: number) =>
    request<GameSummary[]>(`/api/games${folderId ? `?folder_id=${folderId}` : ''}`),
  folderReplays: (folderId: number) =>
    request<FolderReplay[]>(`/api/folders/${folderId}/replays`),
  game: (gameId: number) => request<GameDetail>(`/api/games/${gameId}`),
  timeline: (gameId: number, playerId?: number) =>
    request<EventItem[]>(
      `/api/games/${gameId}/timeline${playerId ? `?player_id=${playerId}` : ''}`,
    ),
  buildings: (gameId: number, playerId?: number) =>
    request<EventItem[]>(
      `/api/games/${gameId}/buildings${playerId ? `?player_id=${playerId}` : ''}`,
    ),
  tech: (gameId: number, playerId?: number) =>
    request<TechTiming[]>(
      `/api/games/${gameId}/tech${playerId ? `?player_id=${playerId}` : ''}`,
    ),
  units: (gameId: number, playerId?: number) =>
    request<UnitLifecycle[]>(
      `/api/games/${gameId}/units${playerId ? `?player_id=${playerId}` : ''}`,
    ),
  stats: (gameId: number, playerId?: number) =>
    request<PlayerStat[]>(
      `/api/games/${gameId}/stats${playerId ? `?player_id=${playerId}` : ''}`,
    ),
  createImport: (path: string) =>
    request<ImportJob>('/api/imports', {
      method: 'POST',
      body: JSON.stringify({ path }),
    }),
  importFile: (path: string) =>
    request<{ folder_id: number; game_id: number | null; imported: number; skipped: number }>(
      '/api/imports/file',
      {
        method: 'POST',
        body: JSON.stringify({ path }),
      },
    ),
  deleteFolder: (folderId: number) =>
    request<{ deleted: number }>(`/api/folders/${folderId}`, { method: 'DELETE' }),
  imports: () => request<ImportJob[]>('/api/imports'),
  importJob: (id: string) => request<ImportJob>(`/api/imports/${id}`),
}
