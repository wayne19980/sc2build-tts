import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const FILES = {
  rootPackage: join(ROOT, 'package.json'),
  vuePackage: join(ROOT, 'vue-app', 'package.json'),
  tauriConf: join(ROOT, 'vue-app', 'src-tauri', 'tauri.conf.json'),
  cargoToml: join(ROOT, 'vue-app', 'src-tauri', 'Cargo.toml'),
  cargoLock: join(ROOT, 'vue-app', 'src-tauri', 'Cargo.lock'),
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'))
}

function writeJson(path, data) {
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`)
}

function resolveVersion(current, target) {
  const arg = target || 'patch'
  if (/^\d+\.\d+\.\d+$/.test(arg)) return arg

  const match = /^(\d+)\.(\d+)\.(\d+)$/.exec(current)
  if (!match) throw new Error(`current version is not semver: ${current}`)
  const major = Number(match[1])
  const minor = Number(match[2])
  const patch = Number(match[3])

  if (arg === 'major') return `${major + 1}.0.0`
  if (arg === 'minor') return `${minor + 1}.0`
  if (arg === 'patch') return `${major}.${minor}.${patch + 1}`
  throw new Error(`unknown version target: ${arg} (use x.y.z, patch, minor or major)`)
}

function replacePackageVersion(path, version) {
  if (!existsSync(path)) return false
  const pkg = readJson(path)
  if (typeof pkg.version !== 'string') return false
  pkg.version = version
  writeJson(path, pkg)
  return true
}

function replaceTauriVersion(path, version) {
  const conf = readJson(path)
  conf.version = version
  writeJson(path, conf)
}

function replaceCargoTomlVersion(path, version) {
  const source = readFileSync(path, 'utf8')
  const index = source.indexOf('[package]')
  if (index < 0) throw new Error(`${path}: missing [package] section`)
  const head = source.slice(0, index)
  const body = source.slice(index)
  const pattern = /^version = "[^"]+"/m
  if (!pattern.test(body)) throw new Error(`${path}: package version not found`)
  writeFileSync(path, head + body.replace(pattern, `version = "${version}"`))
}

function replaceCargoLockVersion(path, version) {
  if (!existsSync(path)) return false
  const source = readFileSync(path, 'utf8')
  const pattern = /(\[\[package\]\]\r?\nname = "app"\r?\nversion = ")[^"]+(")/
  if (!pattern.test(source)) throw new Error(`${path}: package "app" not found`)
  writeFileSync(path, source.replace(pattern, `$1${version}$2`))
  return true
}

const current = readJson(FILES.vuePackage).version
const version = resolveVersion(current, process.argv[2])

const updated = []
if (replacePackageVersion(FILES.rootPackage, version)) updated.push('package.json')
if (replacePackageVersion(FILES.vuePackage, version)) updated.push('vue-app/package.json')
replaceTauriVersion(FILES.tauriConf, version)
updated.push('vue-app/src-tauri/tauri.conf.json')
replaceCargoTomlVersion(FILES.cargoToml, version)
updated.push('vue-app/src-tauri/Cargo.toml')
if (replaceCargoLockVersion(FILES.cargoLock, version)) {
  updated.push('vue-app/src-tauri/Cargo.lock')
}

console.log(`bumped ${current} -> ${version}`)
console.log(`updated: ${updated.join(', ')}`)
