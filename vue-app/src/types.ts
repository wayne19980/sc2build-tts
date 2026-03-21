/** Raw build order item from Python parser */
export interface RawBuildItem {
  start_time: number
  supply: number | string
  unit: string
  _kind: 'upgrade' | 'unit'
  is_worker: boolean
}

/** A player within a team */
export interface PlayerData {
  name: string
  race: string  // 'T' | 'P' | 'Z' | '?'
  build_order: RawBuildItem[]
}

/** A team containing players */
export interface TeamData {
  players: PlayerData[]
}

/** Chat message */
export interface ChatMessage {
  time: number
  player: string
  pid: number | null
  target: string
  text: string
}

/** Full replay data from Python parser */
export interface ReplayData {
  map_name: string
  game_length: number // seconds
  client_version: string
  region: string
  start_time: number | null // unix timestamp
  winner: string | null
  teams: TeamData[]
  chat: ChatMessage[]
}

/** Processed build item for display */
export interface ProcessedBuildItem {
  timeStr: string
  supplyStr: string
  unitText: string
  extraClass: string
  raw: RawBuildItem
}

/** Voice step for TTS */
export interface VoiceStep {
  time: number  // real seconds
  text: string
  speech: string
}
