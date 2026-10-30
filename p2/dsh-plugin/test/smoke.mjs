/**
 * dsh-butler-tools 离线冒烟测试（不属于插件本身，仅验证壳的 argv 组装与透传）。
 * 用一个假的 cordis ctx 收集工具定义，并用 node:child_process 充当
 * subprocess 服务，真实调用 python 内核。
 *
 *   node lib/../test/smoke.mjs            # 跑默认用例
 */
import { spawn } from 'node:child_process'
import { closeSync, openSync, readFileSync, rmSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import path from 'node:path'

const here = path.dirname(fileURLToPath(import.meta.url))
const modulePath = pathToFileURL(path.resolve(here, '../lib/index.js')).href
const runDir = path.resolve(here, '..')

/** 读完整流：dsh 的沙箱禁止管道式 stdio，这里改用文件描述符捕获。 */
function readAndDrop(filePath) {
  try {
    return readFileSync(filePath, 'utf8')
  } catch {
    return ''
  } finally {
    try {
      rmSync(filePath, { force: true })
    } catch {
      // 忽略清理失败
    }
  }
}

/** 最小 subprocess 服务替身：只实现插件用到的 spawn 契约。 */
let lastArgv = []
let runSeq = 0
const fakeSubprocess = {
  spawn(spec) {
    lastArgv = [...spec.argv]
    runSeq += 1
    const outPath = path.join(runDir, `.smoke-${runSeq}.out`)
    const errPath = path.join(runDir, `.smoke-${runSeq}.err`)
    const outFd = openSync(outPath, 'w')
    const errFd = openSync(errPath, 'w')
    const child = spawn(spec.argv[0], spec.argv.slice(1), {
      cwd: spec.cwd,
      env: { ...process.env, ...(spec.env ?? {}) },
      stdio: ['ignore', outFd, errFd],
      signal: spec.signal,
      windowsHide: true,
    })
    closeSync(outFd)
    closeSync(errFd)
    let captured = null
    const done = new Promise((resolve, reject) => {
      child.on('error', reject)
      child.on('close', (exitCode, signal) => {
        captured = { stdout: readAndDrop(outPath), stderr: readAndDrop(errPath) }
        resolve({ exitCode, signal })
      })
    })
    return {
      pid: child.pid,
      collected: {
        stdout: { readFrom: () => ({ text: captured === null ? '' : captured.stdout, nextOffset: 0, lossy: false }) },
        stderr: { readFrom: () => ({ text: captured === null ? '' : captured.stderr, nextOffset: 0, lossy: false }) },
      },
      done,
      terminate() { child.kill() },
      waitForExit() { return done.then(() => true) },
    }
  },
}

const registered = new Map()
const ctx = {
  tools: {
    register(definition) {
      registered.set(definition.name, definition)
      return () => registered.delete(definition.name)
    },
  },
  get(name) {
    return name === 'subprocess' ? fakeSubprocess : undefined
  },
}

const mod = await import(modulePath)
if (typeof mod.apply !== 'function') throw new Error('module must export apply()')
if (mod.name !== 'dsh-butler-tools') throw new Error('unexpected plugin name: ' + String(mod.name))
mod.apply(ctx)

const expected = [
  'butler_ask', 'butler_profile', 'butler_preferences', 'butler_reveal', 'butler_verify',
  'butler_schedule', 'butler_summary', 'butler_add_event', 'butler_add_highlight',
  'butler_add_skills', 'butler_regen', 'butler_jobs_add', 'butler_jobs',
  'butler_jobs_status', 'butler_match',
]
const missing = expected.filter((toolName) => !registered.has(toolName))
const extra = [...registered.keys()].filter((toolName) => !expected.includes(toolName))
console.log(`registered=${registered.size} missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`)
if (registered.size !== 15 || missing.length !== 0 || extra.length !== 0) {
  throw new Error('tool table is not 1:1 with the 15 subcommands')
}

/** 直接执行一个工具，走完整 execute → render 链路。 */
async function call(toolName, args) {
  const definition = registered.get(toolName)
  lastArgv = null
  const value = await definition.execute(args, { signal: undefined })
  const content = definition.output.render(args, value)
  return { value, text: content.map((block) => block.text).join('\n'), argv: lastArgv }
}

const summary = await call('butler_summary', {})
console.log('\n[butler_summary] keys=' + Object.keys(summary.value).join(',')
  + ' events=' + summary.value.events.length
  + ' silicon=' + summary.value.skills_silicon)

const answer = await call('butler_ask', { question: '做过AI平台建设吗' })
console.log('[butler_ask] evidence=' + answer.value.evidence.length
  + ' answerHead=' + JSON.stringify(answer.value.answer.slice(0, 18)))

const jobs = await call('butler_jobs', {})
console.log('[butler_jobs] count=' + jobs.value.jobs.length)

const missingArg = await registered.get('butler_match').execute({}, { signal: undefined })
  .then(() => 'RESOLVED (unexpected)')
  .catch((error) => error.message)
console.log('[butler_match without job_id] ' + missingArg)

// 编译/渲染一致性：render 输出的文本必须是同一份 JSON。
const roundTrip = JSON.parse(summary.text)
if (JSON.stringify(roundTrip) !== JSON.stringify(summary.value)) {
  throw new Error('render output is not the same JSON as the canonical value')
}
console.log('[render] passthrough JSON identical to canonical value')

// argv 组装：位置参数在前、旗标在后、--object 收尾，解释器/CLI 路径固定。
console.log('[argv] ask=' + JSON.stringify(answer.argv))
const expectedArgv = [
  'C:/Users/EDY/AppData/Local/Python/bin/python.exe',
  'C:/Users/EDY/.kimi/dossier/p2/butler_cli.py',
  'ask', '做过AI平台建设吗',
  '--object', 'C:/Users/EDY/.dsh/career-butler/talent-object.json',
]
if (JSON.stringify(answer.argv) !== JSON.stringify(expectedArgv)) {
  throw new Error('argv mismatch: ' + JSON.stringify(answer.argv))
}
console.log('[argv] 与 CLI 契约一致')

console.log('\nSMOKE OK')
