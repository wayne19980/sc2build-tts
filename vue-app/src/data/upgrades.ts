import type { EventItem, Race, TechTiming } from '../types-analysis'
import { resolveItem, type CatalogItem } from './catalog'

/**
 * Which building researches which upgrades. Used to echo the upgrade strip
 * next to the matching building node in the tech tree.
 * Keys must match `TreeBuilding.key` in `tech-trees.json`.
 */
export const UPGRADE_BUILDINGS: Record<Race, Record<string, string[]>> = {
  P: {
    Forge: [
      'ProtossGroundWeaponsLevel1',
      'ProtossGroundWeaponsLevel2',
      'ProtossGroundWeaponsLevel3',
      'ProtossGroundArmorsLevel1',
      'ProtossGroundArmorsLevel2',
      'ProtossGroundArmorsLevel3',
      'ProtossPlasmaShieldsLevel1',
      'ProtossPlasmaShieldsLevel2',
      'ProtossPlasmaShieldsLevel3',
    ],
    CyberneticsCore: [
      'WarpGateResearch',
      'ProtossAirWeaponsLevel1',
      'ProtossAirWeaponsLevel2',
      'ProtossAirWeaponsLevel3',
      'ProtossAirArmorsLevel1',
      'ProtossAirArmorsLevel2',
      'ProtossAirArmorsLevel3',
    ],
    TwilightCouncil: ['Charge', 'BlinkTech', 'ResonatingGlaives'],
    TemplarArchive: ['PsiStormTech'],
    DarkShrine: ['ShadowStride'],
    RoboticsBay: ['GraviticDrive', 'GraviticBoosters', 'ExtendedThermalLance'],
    FleetBeacon: ['AnionPulseCrystals', 'FluxVanes', 'TectonicDestabilizers'],
  },
  T: {
    Barracks: ['Stimpack', 'ShieldWall', 'PunisherGrenades'],
    EngineeringBay: [
      'NeosteelArmor',
      'HiSecAutoTracking',
      'TerranInfantryWeaponsLevel1',
      'TerranInfantryWeaponsLevel2',
      'TerranInfantryWeaponsLevel3',
      'TerranInfantryArmorsLevel1',
      'TerranInfantryArmorsLevel2',
      'TerranInfantryArmorsLevel3',
    ],
    GhostAcademy: ['PersonalCloaking'],
    Factory: ['DrillClaws', 'InfernalPreigniter', 'MagFieldAccelerator', 'SmartServos'],
    Starport: [
      'CaduceusReactor',
      'AdvancedBallistics',
      'HyperflightRotors',
      'CloakingField',
      'InterferenceMatrix',
    ],
    FusionCore: ['YamatoCannon'],
    Armory: [
      'TerranVehicleWeaponsLevel1',
      'TerranVehicleWeaponsLevel2',
      'TerranVehicleWeaponsLevel3',
      'TerranShipWeaponsLevel1',
      'TerranShipWeaponsLevel2',
      'TerranShipWeaponsLevel3',
      'TerranVehicleAndShipArmorsLevel1',
      'TerranVehicleAndShipArmorsLevel2',
      'TerranVehicleAndShipArmorsLevel3',
    ],
  },
  Z: {
    Hatchery: ['Burrow', 'PneumatizedCarapace', 'VentralSacs'],
    SpawningPool: ['MetabolicBoost', 'AdrenalGlands'],
    BanelingNest: ['CentrifugalHooks'],
    RoachWarren: ['GlialReconstitution', 'TunnelingClaws'],
    HydraliskDen: ['GroovedSpines', 'MuscularAugments'],
    LurkerDen: ['AdaptiveTalons', 'SeismicSpines'],
    InfestationPit: ['NeuralParasite', 'MicrobialShroud'],
    UltraliskCavern: ['ChitinousPlating', 'AnabolicSynthesis'],
    EvolutionChamber: [
      'ZergMeleeWeaponsLevel1',
      'ZergMeleeWeaponsLevel2',
      'ZergMeleeWeaponsLevel3',
      'ZergMissileWeaponsLevel1',
      'ZergMissileWeaponsLevel2',
      'ZergMissileWeaponsLevel3',
      'ZergGroundArmorsLevel1',
      'ZergGroundArmorsLevel2',
      'ZergGroundArmorsLevel3',
    ],
    Spire: [
      'ZergFlyerWeaponsLevel1',
      'ZergFlyerWeaponsLevel2',
      'ZergFlyerWeaponsLevel3',
      'ZergFlyerArmorsLevel1',
      'ZergFlyerArmorsLevel2',
      'ZergFlyerArmorsLevel3',
    ],
    GreaterSpire: [
      'ZergFlyerWeaponsLevel1',
      'ZergFlyerWeaponsLevel2',
      'ZergFlyerWeaponsLevel3',
      'ZergFlyerArmorsLevel1',
      'ZergFlyerArmorsLevel2',
      'ZergFlyerArmorsLevel3',
    ],
  },
}

export interface UpgradeState {
  /** Completion time, only once the timeline has passed it. */
  doneAt?: number
  /** Latest order time for this upgrade. */
  startedAt?: number
  /** Ordered but not finished yet. */
  active: boolean
  progress: number
  indeterminate: boolean
}

/**
 * Merge finished timings with build orders into one state per upgrade key.
 * Shared by the upgrade strip and the per-building upgrade chips.
 */
export function computeUpgradeStates(
  tech: TechTiming[],
  orders: EventItem[],
  time: number,
): Record<string, UpgradeState> {
  const completions: Record<string, number> = {}
  for (const timing of tech) {
    const item = resolveItem(timing.tech)
    if (!item || item.kind !== 'upgrade') continue
    const current = completions[item.key]
    if (current === undefined || timing.t_sec < current) completions[item.key] = timing.t_sec
  }

  const starts: Record<string, number> = {}
  for (const order of orders) {
    if (order.kind !== 'order') continue
    const item = resolveItem(order.name)
    if (!item || item.kind !== 'upgrade') continue
    const current = starts[item.key]
    if (current === undefined || order.t_sec > current) starts[item.key] = order.t_sec
  }

  const result: Record<string, UpgradeState> = {}
  const keys = new Set([...Object.keys(starts), ...Object.keys(completions)])
  for (const key of keys) {
    const start = starts[key]
    const done = completions[key]
    const doneAt = done !== undefined && done <= time ? done : undefined
    const active = start !== undefined && start <= time && (done === undefined || done > time)
    const progress =
      active && done !== undefined && done > start
        ? Math.min(1, Math.max(0, (time - start) / (done - start)))
        : 0
    result[key] = {
      doneAt,
      startedAt: start,
      active,
      progress,
      indeterminate: active && done === undefined,
    }
  }
  return result
}
const LEVEL_UPGRADE_FAMILIES: string[][] = [
  ['ProtossGroundWeaponsLevel1', 'ProtossGroundWeaponsLevel2', 'ProtossGroundWeaponsLevel3'],
  ['ProtossGroundArmorsLevel1', 'ProtossGroundArmorsLevel2', 'ProtossGroundArmorsLevel3'],
  ['ProtossPlasmaShieldsLevel1', 'ProtossPlasmaShieldsLevel2', 'ProtossPlasmaShieldsLevel3'],
  ['ProtossAirWeaponsLevel1', 'ProtossAirWeaponsLevel2', 'ProtossAirWeaponsLevel3'],
  ['ProtossAirArmorsLevel1', 'ProtossAirArmorsLevel2', 'ProtossAirArmorsLevel3'],
  ['TerranInfantryWeaponsLevel1', 'TerranInfantryWeaponsLevel2', 'TerranInfantryWeaponsLevel3'],
  ['TerranInfantryArmorsLevel1', 'TerranInfantryArmorsLevel2', 'TerranInfantryArmorsLevel3'],
  ['TerranVehicleWeaponsLevel1', 'TerranVehicleWeaponsLevel2', 'TerranVehicleWeaponsLevel3'],
  ['TerranShipWeaponsLevel1', 'TerranShipWeaponsLevel2', 'TerranShipWeaponsLevel3'],
  [
    'TerranVehicleAndShipArmorsLevel1',
    'TerranVehicleAndShipArmorsLevel2',
    'TerranVehicleAndShipArmorsLevel3',
  ],
  ['ZergMeleeWeaponsLevel1', 'ZergMeleeWeaponsLevel2', 'ZergMeleeWeaponsLevel3'],
  ['ZergMissileWeaponsLevel1', 'ZergMissileWeaponsLevel2', 'ZergMissileWeaponsLevel3'],
  ['ZergGroundArmorsLevel1', 'ZergGroundArmorsLevel2', 'ZergGroundArmorsLevel3'],
  ['ZergFlyerWeaponsLevel1', 'ZergFlyerWeaponsLevel2', 'ZergFlyerWeaponsLevel3'],
  ['ZergFlyerArmorsLevel1', 'ZergFlyerArmorsLevel2', 'ZergFlyerArmorsLevel3'],
]

const levelFamily = new Map<string, string[]>()
for (const family of LEVEL_UPGRADE_FAMILIES) {
  for (const key of family) levelFamily.set(key, family)
}

export interface CollapsedUpgrade {
  item: CatalogItem
  activeItem?: CatalogItem
  doneAt?: number
  active: boolean
  progress: number
  indeterminate: boolean
}

/**
 * Attack/armor upgrades have three level icons. Collapse a family to the
 * highest completed level, and show a higher level that is being researched
 * on the same chip.
 */
export function collapseUpgradeKeys(
  keys: string[],
  states: Record<string, UpgradeState>,
): CollapsedUpgrade | undefined {
  const levels = keys
    .map((key, index) => ({ key, index, item: resolveItem(key) }))
    .filter(
      (level): level is { key: string; index: number; item: CatalogItem } =>
        Boolean(level.item),
    )
  if (!levels.length) return undefined

  const done = levels
    .filter((level) => states[level.key]?.doneAt !== undefined)
    .sort((a, b) => b.index - a.index)[0]
  const active = levels
    .filter((level) => states[level.key]?.active)
    .sort((a, b) => b.index - a.index)[0]
  const display = done ?? active ?? levels[0]
  const activeItem =
    active && (!done || active.index > done.index) ? active.item : undefined
  const activeState = activeItem && active ? states[active.key] : undefined

  return {
    item: display.item,
    activeItem,
    doneAt: done ? states[done.key]?.doneAt : undefined,
    active: Boolean(activeItem),
    progress: activeState?.progress || 0,
    indeterminate: Boolean(activeState?.indeterminate),
  }
}

export function collapseUpgrades(
  items: CatalogItem[],
  states: Record<string, UpgradeState>,
): CollapsedUpgrade[] {
  const result: CollapsedUpgrade[] = []
  const seenFamilies = new Set<string>()

  for (const item of items) {
    const family = levelFamily.get(item.key)
    if (family) {
      if (seenFamilies.has(family[0])) continue
      seenFamilies.add(family[0])
      const collapsed = collapseUpgradeKeys(family, states)
      if (collapsed) result.push(collapsed)
      continue
    }
    const collapsed = collapseUpgradeKeys([item.key], states)
    if (collapsed) result.push(collapsed)
  }
  return result
}
