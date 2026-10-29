export type Race = 'P' | 'T' | 'Z'

export interface FolderInfo {
  id: number
  path: string
  name: string
  created_at: string
  game_count: number
  last_played: string | null
}

export interface GameSummary {
  game_id: number
  folder_id: number
  folder_name: string
  folder_path: string
  file_name: string
  map_name: string | null
  duration_sec: number | null
  played_at: string | null
  game_version: string | null
  region: string | null
  game_type: string | null
  players: string | null
  winner: string | null
}

export interface PlayerInfo {
  id: number
  pid: number
  name: string
  race: string | null
  team: number | null
  result: string | null
  is_winner: boolean
  is_human: boolean
  uid: number | null
  color: string | null
}

export interface EventItem {
  game_id: number
  player_id: number
  player_name: string
  race: string
  frame: number
  t_sec: number
  kind: string
  name: string
  display_name: string | null
  supply: number | null
  is_worker: boolean
  payload: Record<string, unknown>
}

export interface SupplyInfo {
  used: number
  made: number
  workers: number
  army: number
}

export interface PlayerStat {
  game_id: number
  player_id: number
  player_name: string
  race: string
  frame: number
  t_sec: number
  minerals: number | null
  vespene: number | null
  workers: number | null
  supply_used: number | null
  supply_made: number | null
  army_value: number | null
  minerals_collection_rate: number | null
  vespene_collection_rate: number | null
  resources_lost: number | null
  resources_killed: number | null
}

export interface UnitMorph {
  t_sec: number
  from: string
  to: string
}

export interface UnitLifecycle {
  game_id: number
  player_id: number
  player_name: string
  race: string
  unit_id: number
  first_type: string
  unit_type: string
  born_t_sec: number
  died_t_sec: number | null
  is_worker: boolean
  is_army: boolean
  is_building: boolean
  morphs: UnitMorph[]
  payload: Record<string, unknown>
}

export interface TechTiming {
  game_id: number
  player_id: number
  player_name: string
  race: string
  t_sec: number
  frame: number
  tech: string
  payload: Record<string, unknown>
}

export interface GameDetail {
  game: GameSummary
  players: PlayerInfo[]
  event_counts: { kind: string; count: number }[]
}

export type ImportMode = 'current' | 'group' | 'merge'

export interface ImportJob {
  id: string
  path: string
  status: 'queued' | 'running' | 'done' | 'failed'
  phase: string
  total: number
  processed: number
  progress: number
  current_file: string | null
  imported: number
  skipped: number
  errors: string[]
  created_at: string
  started_at: string | null
  finished_at: string | null
  message: string | null
}

export type OverlayAnchor = 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-right'

export interface OverlayState {
  gameId: number | null
  playerId: number | null
  playerName: string
  mapName: string
  race: Race | null
  time: number
  duration: number
  countMode: 'cumulative' | 'alive'
  opacity: number
  english: boolean
  includeWorkers: boolean
}

export interface ReplayUnitCount {
  unit: string
  count: number
}

export interface ReplayTechTiming {
  tech: string
  t_sec: number
}

export interface ReplayTechPhases {
  early: ReplayTechTiming[]
  mid: ReplayTechTiming[]
  late: ReplayTechTiming[]
}

export interface FolderReplayPlayer {
  id: number
  game_id: number
  pid: number
  name: string
  race: string | null
  result: string | null
  is_winner: boolean
  units: ReplayUnitCount[]
  buildings?: ReplayBuildingCount[]
  tech: ReplayTechPhases
}

export interface FolderReplay extends GameSummary {
  player_details: FolderReplayPlayer[]
}

export interface VoiceStep {
  time: number
  text: string
  speech: string
}

export interface ConstructionGroupView {
  key: string
  name: string
  icon: string
  count: number
  progress: number
  indeterminate: boolean
}

export interface ConstructionStripView {
  key: string
  playerName: string
  race?: Race
  /** Player tint used by the split view; null keeps the neutral blue frame. */
  tint: 'red' | 'blue' | null
  groups: ConstructionGroupView[]
}

export interface UpgradeStripRow {
  key: string
  playerName: string
  /** Player tint used by the split view; null keeps the neutral blue frame. */
  tint: 'red' | 'blue' | null
  race: Race
  tech: TechTiming[]
  orders: EventItem[]
}

export interface ProductionTaskView {
  key: string
  name: string
  start: number
  done: number | null
}

export interface ReplayBuildingCount {
  building: string
  count: number
}
