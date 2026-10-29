import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ANALYZER = join(ROOT, 'services', 'analyzer')
const isWindows = process.platform === 'win32'
const API_URL = 'http://127.0.0.1:8765/api/health'

function resolvePython() {
  const candidates = isWindows
    ? [join(ROOT, '.venv', 'Scripts', 'python.exe')]
    : [join(ROOT, '.venv', 'bin', 'python')]
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate
  }
  return isWindows ? 'python' : 'python3'
}

async function apiIsUp() {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 800)
    const response = await fetch(API_URL, { signal: controller.signal })
    clearTimeout(timer)
    return response.ok
  } catch {
    return false
  }
}

function killTree(child) {
  if (!child?.pid) return
  if (isWindows) {
    spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' })
  } else {
    child.kill('SIGTERM')
  }
}

const children = []
let shuttingDown = false

function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true
  for (const child of children) killTree(child)
  process.exit(code)
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

function track(child, name) {
  children.push(child)
  child.on('exit', (code) => {
    if (shuttingDown) return
    console.error(`\n[${name}] exited with code ${code ?? 'unknown'}`)
    shutdown(code ?? 1)
  })
  return child
}

if (await apiIsUp()) {
  console.log('Python API already running on 127.0.0.1:8765')
} else {
  console.log('Starting Python API on 127.0.0.1:8765…')
  track(
    spawn(resolvePython(), ['run_api.py'], {
      cwd: ANALYZER,
      stdio: 'inherit',
      env: {
        ...process.env,
        PYTHONPATH: ANALYZER,
        SC2_ENV_FILE: join(ROOT, '.env'),
        SC2_API_HOST: '127.0.0.1',
        SC2_API_PORT: '8765',
      },
    }),
    'api',
  )
  // Give migrations a moment before Vite starts hammering /api.
  await new Promise((resolve) => setTimeout(resolve, 1500))
}

console.log('Starting Vite dev server on http://127.0.0.1:5173…')
track(
  spawn('pnpm --dir vue-app dev', {
    cwd: ROOT,
    stdio: 'inherit',
    shell: true,
  }),
  'vite',
)
