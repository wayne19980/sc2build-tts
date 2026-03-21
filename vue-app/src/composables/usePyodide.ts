import { ref } from 'vue'
import type { ReplayData } from '../types'

declare global {
  interface Window {
    loadPyodide?: (options: { indexURL: string }) => Promise<any>
  }
}

const PYODIDE_VERSION = '0.29.3'

const PARSE_SCRIPT = `
import json
import sc2reader
from sc2reader.events.message import ChatEvent
import spawningtool.parser

def extract_replay_data(replay_path):
    def patched_get_display_name(self, unit_name, player):
        return unit_name
    spawningtool.parser.GameParser.get_display_name = patched_get_display_name

    parser = spawningtool.parser.GameParser(replay_path)
    st_data = parser.get_parsed_data()
    replay = parser.replay
    
    start_time_ts = None
    if hasattr(replay, 'start_time'):
        try:
            start_time_ts = int(replay.start_time.timestamp())
        except:
            pass

    result = {
        "map_name": st_data.get("map", "Unknown"),
        "game_length": st_data.get("frames", 0) // st_data.get("frames_per_second", 16),
        "client_version": st_data.get("build"),
        "region": st_data.get("region"),
        "start_time": start_time_ts,
        "winner": None,
        "teams": [],
        "chat": [],
    }

    for ev in getattr(replay, "events", []):
        if isinstance(ev, ChatEvent):
            frame = int(getattr(ev, "frame", 0))
            sec = frame >> 4
            result["chat"].append({
                "time": int(sec),
                "player": getattr(ev.player, "name", ""),
                "pid": getattr(ev, "pid", None),
                "target": getattr(ev, "target", ""),
                "text": getattr(ev, "text", ""),
            })

    winners = []
    for team in getattr(replay, "teams", []):
        if getattr(team, "result", None) == "Win":
            winners.append(" & ".join([p.name for p in team.players]))
    if winners:
        result["winner"] = " / ".join(winners)

    for team in replay.teams:
        team_data = {"players": []}
        for player in team.players:
            st_player = st_data["players"].get(player.pid)
            if not st_player: continue
                
            build_order = []
            for item in st_player.get("buildOrder", []):
                build_order.append({
                    "start_time": int(item["frame"]) >> 4,
                    "supply": item["supply"],
                    "unit": item["name"],
                    "_kind": "upgrade" if item.get("type") == "Upgrade" else "unit",
                    "is_worker": item.get("is_worker", False)
                })
            
            team_data["players"].append({
                "name": player.name,
                "race": (player.pick_race or "?")[0],
                "build_order": build_order,
            })
        result["teams"].append(team_data)
    return result
`

export function usePyodide() {
  const pyodide = ref<any>(null)
  const initStatus = ref('正在加载 Python 运行环境...')
  const initProgress = ref('初始化中')
  const isReady = ref(false)
  const isLoading = ref(false)
  const errorMsg = ref('')

  async function ensureScriptLoaded(): Promise<void> {
    if (typeof window.loadPyodide === 'function') return Promise.resolve()

    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('无法加载 Pyodide 脚本，请检查网络连接'))
      document.head.appendChild(script)
    })
  }

  async function init() {
    try {
      initProgress.value = '正在下载 Pyodide 脚本...'
      await ensureScriptLoaded()

      initProgress.value = '加载 Pyodide 运行时...'

      const indexURL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`
      if (!window.loadPyodide) throw new Error('Pyodide 脚本加载失败')
      pyodide.value = await window.loadPyodide({ indexURL })

      initProgress.value = '安装 mpyq（从源码）...'
      const mpyqResp = await fetch(
        'https://cdn.jsdelivr.net/gh/eagleflo/mpyq@master/mpyq.py',
      )
      if (!mpyqResp.ok) throw new Error('mpyq 下载失败: ' + mpyqResp.status)
      const mpyqCode = await mpyqResp.text()
      pyodide.value.FS.mkdirTree('/tmp')
      pyodide.value.FS.writeFile('/tmp/mpyq.py', new TextEncoder().encode(mpyqCode))
      await pyodide.value.runPythonAsync(`
import sys
sys.path.insert(0, "/tmp")
import mpyq
`)

      initProgress.value = '安装 sc2reader & spawningtool...'
      await pyodide.value.loadPackage('micropip')
      await pyodide.value.runPythonAsync(`
import micropip
await micropip.install('sc2reader', deps=False)
await micropip.install('spawningtool', deps=False)
`)

      isReady.value = true
      initStatus.value = ''
    } catch (e: any) {
      console.error(e)
      errorMsg.value = `初始化失败: ${e.message}`
    }
  }

  async function parseReplay(file: File): Promise<ReplayData | null> {
    if (!pyodide.value) return null
    isLoading.value = true
    errorMsg.value = ''

    try {
      const buffer = await file.arrayBuffer()
      const data = new Uint8Array(buffer)

      pyodide.value.FS.writeFile('/tmp/replay.SC2Replay', data)

      const parseCode = `
${PARSE_SCRIPT}
result = extract_replay_data("/tmp/replay.SC2Replay")
json.dumps(result)
`
      const resultJson = await pyodide.value.runPythonAsync(parseCode)
      const parsed: ReplayData = JSON.parse(resultJson)

      pyodide.value.FS.unlink('/tmp/replay.SC2Replay')

      return parsed
    } catch (e: any) {
      console.error(e)
      errorMsg.value = e.message || '解析失败，请检查文件格式'
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    initStatus,
    initProgress,
    isReady,
    isLoading,
    errorMsg,
    init,
    parseReplay,
  }
}
