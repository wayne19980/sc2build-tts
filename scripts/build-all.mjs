import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const isWindows = process.platform === 'win32'

function resolvePython() {
  const candidates = isWindows
    ? [join(ROOT, '.venv', 'Scripts', 'python.exe')]
    : [join(ROOT, '.venv', 'bin', 'python')]
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate
  }
  return isWindows ? 'python' : 'python3'
}

function run(command, args) {
  console.log(`\n$ ${command} ${args.join(' ')}`)
  const result = spawnSync(command, args, { cwd: ROOT, stdio: 'inherit' })
  if (result.error) throw result.error
  if (result.status !== 0) process.exit(result.status ?? 1)
}

function runShell(command) {
  console.log(`\n$ ${command}`)
  const result = spawnSync(command, { cwd: ROOT, stdio: 'inherit', shell: true })
  if (result.error) throw result.error
  if (result.status !== 0) process.exit(result.status ?? 1)
}

run(resolvePython(), [join('scripts', 'build_sidecar.py')])
runShell('pnpm --dir vue-app tauri:build')
