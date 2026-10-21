import type { Race } from '../types-analysis'
import { techTrees } from './catalog'

export const CELL_W = 300
export const CELL_W_COMPACT = 230
// Rows also carry the upgrade chips that hang under each building icon.
export const ROW_H = 112
export const MARGIN = 20

export function treeSize(race: Race, cellWidth = CELL_W): { width: number; height: number } {
  const tree = techTrees[race]
  const maxX = Math.max(...tree.buildings.map((building) => building.x))
  const maxY = Math.max(...tree.buildings.map((building) => building.y))
  const extraRow = tree.otherUnits.length > 0 ? 2 : 1
  return {
    width: (maxX + 1) * cellWidth + MARGIN * 2,
    height: (maxY + extraRow) * ROW_H + MARGIN * 2,
  }
}
