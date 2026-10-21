import rawCatalog from './sc2-catalog.json'
import rawTrees from './tech-trees.json'
import type { Race } from '../types-analysis'

export type CatalogKind = 'building' | 'unit' | 'upgrade'

export interface CatalogItem {
  key: string
  abbr: string
  name: string
  nameZh: string
  kind: CatalogKind
  race: Race
  aliases: string[]
  icon?: string
}

export interface TreeBuilding {
  key: string
  x: number
  y: number
  requires: string[]
}

export interface TreeUnit {
  key: string
  requiresAny: string[]
}

export interface TreeUnitGroup {
  group: string
  units: TreeUnit[]
}

export interface TechTree {
  name: string
  nameZh: string
  buildings: TreeBuilding[]
  unitGroups: TreeUnitGroup[]
  otherUnits: TreeUnit[]
}

export const catalog = rawCatalog as Record<string, CatalogItem>
export const techTrees = rawTrees as Record<Race, TechTree>

export const catalogByKey = new Map(Object.entries(catalog))

const aliases = new Map<string, CatalogItem>()
for (const item of Object.values(catalog)) {
  aliases.set(item.key, item)
  for (const alias of item.aliases) aliases.set(alias, item)
}

const rawAliases: Record<string, string> = {
  zerglingmovementspeed: 'MetabolicBoost',
  zerglingattackspeed: 'AdrenalGlands',
  CentrificalHooks: 'CentrifugalHooks',
  overlordspeed: 'PneumatizedCarapace',
  EvolveMuscularAugments: 'MuscularAugments',
  EvolveGroovedSpines: 'GroovedSpines',
  DiggingClaws: 'AdaptiveTalons',
  LurkerRange: 'SeismicSpines',
  ProtossShieldsLevel1: 'ProtossPlasmaShieldsLevel1',
  ProtossShieldsLevel2: 'ProtossPlasmaShieldsLevel2',
  ProtossShieldsLevel3: 'ProtossPlasmaShieldsLevel3',
  AdeptPiercingAttack: 'ResonatingGlaives',
  HighCapacityBarrels: 'InfernalPreigniter',
  TerranBuildingArmor: 'NeosteelArmor',
  PhoenixRangeUpgrade: 'AnionPulseCrystals',
  VoidRaySpeedUpgrade: 'FluxVanes',
  CycloneLockOnDamageUpgrade: 'MagFieldAccelerator',
  MedivacCaduceusReactor: 'CaduceusReactor',
  HellionTank: 'Hellbat',
}
for (const [alias, target] of Object.entries(rawAliases)) {
  const item = catalog[target]
  if (item) aliases.set(alias, item)
}

export function resolveItem(name: string | null | undefined): CatalogItem | undefined {
  if (!name) return undefined
  return aliases.get(name)
}

export function iconUrl(abbr: string): string {
  return `${import.meta.env.BASE_URL}sc2-icons/${abbr}.png`
}

export function itemIconUrl(item: CatalogItem): string {
  return iconUrl(item.icon || item.abbr)
}

export function raceFromName(race: string | null | undefined): Race | null {
  if (!race) return null
  const first = race.trim()[0]?.toUpperCase()
  if (first === 'P' || first === 'T' || first === 'Z') return first
  if (race === 'Protoss') return 'P'
  if (race === 'Terran') return 'T'
  if (race === 'Zerg') return 'Z'
  return null
}

export function formatClock(seconds: number): string {
  const safe = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(safe / 60)
  const rest = safe % 60
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
}

export function upgradeItems(race: Race): CatalogItem[] {
  return Object.values(catalog).filter(
    (item) => item.kind === 'upgrade' && item.race === race,
  )
}

export const WORKER_UNITS = new Set(['Probe', 'SCV', 'Drone'])

export const AUTO_SPAWNED_UNITS = new Set([
  'Broodling',
  'AutoTurret',
  'Interceptor',
  'MULE',
  'Locust',
  'LocustMPFlying',
  'Changeling',
  'ChangelingMarine',
  'ChangelingZealot',
  'ChangelingZergling',
  'Larva',
  'Egg',
  'CreepTumor',
  'CreepTumorQueen',
])
