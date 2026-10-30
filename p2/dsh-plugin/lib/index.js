/**
 * dsh-butler-tools — Career-Butler 档案的原生工具壳（Host 平面 Cordis 插件）。
 *
 * 15 个 `butler_*` 工具，`execute()` 一律通过 subprocess 服务调 python 内核 CLI，
 * 把内核 stdout 的 JSON 原样交回模型。本文件不含任何业务逻辑：访问分级、审计、
 * 备份、一次性揭示语义全部在内核 `butler.py` 里；这里也不直接读写档案文件，
 * 只把 `--object` 路径交给内核。
 *
 * 挂载平面：Host（profile bundle 的一行）。工具注册在全局层，任何 agent 会话都能
 * 直接看到，因此不需要任何 agent preset 参与，也不随会话结束而消失。
 */

export const name = 'dsh-butler-tools'
// Static-package context requires services to be declared via inject
// (the dynamic cordis_define form did not). Both are used in apply().
export const inject = ['tools', 'subprocess']

// ---- 内核调用规范（与 PLUGIN_CONTRACT.md 一致）----------------------------

const PYTHON = 'C:/Users/EDY/AppData/Local/Python/bin/python.exe'
const CLI = 'C:/Users/EDY/.kimi/dossier/p2/butler_cli.py'
const OBJECT = 'C:/Users/EDY/.dsh/career-butler/talent-object.json'
const CWD = 'C:/Users/EDY/.kimi/dossier/p2'
const TIMEOUT_MS = 60000
const GRACE_MS = 3000
const MAX_BYTES = 8 * 1024 * 1024

// ---- argv 组装 ------------------------------------------------------------

function present(value) {
  return value !== undefined && value !== null && value !== ''
}

function flag(argv, name, value) {
  if (present(value)) argv.push(name, String(value))
}

function repeated(argv, name, values) {
  if (!Array.isArray(values)) return
  for (const value of values) {
    if (present(value)) argv.push(name, String(value))
  }
}

function command(name, positional, extras) {
  const argv = [PYTHON, CLI, name]
  if (present(positional)) argv.push(String(positional))
  extras(argv)
  argv.push('--object', OBJECT)
  return argv
}

// ---- 内核调用 -------------------------------------------------------------

function collectedText(handle, stream) {
  const collected = handle.collected
  if (collected === undefined || collected === null) return ''
  const reader = collected[stream]
  if (reader === undefined || typeof reader.readFrom !== 'function') return ''
  const read = reader.readFrom(0)
  return read !== undefined && typeof read.text === 'string' ? read.text : ''
}

async function callKernel(ctx, argv, exec) {
  const subprocess = ctx.get('subprocess')
  if (subprocess === undefined || subprocess === null) {
    throw new Error('butler kernel unavailable: the host subprocess service is not mounted, so '
      + CLI + ' cannot be started.')
  }

  // 内核超时 60s；模型侧取消（exec.signal）同时生效，两者都走 subprocess 的
  // abort→terminate 升级，不需要在 JS 里另起定时器。
  const deadline = AbortSignal.timeout(TIMEOUT_MS)
  const callerSignal = exec !== undefined && exec !== null && exec.signal ? exec.signal : undefined
  const signal = callerSignal === undefined ? deadline : AbortSignal.any([deadline, callerSignal])

  const handle = subprocess.spawn({
    argv,
    cwd: CWD,
    stdio: {
      stdin: 'ignore',
      stdout: { maxBytes: MAX_BYTES },
      stderr: { maxBytes: MAX_BYTES },
    },
    graceMs: GRACE_MS,
    env: { PYTHONIOENCODING: 'utf-8' },
    signal,
  })

  let outcome
  try {
    outcome = await handle.done
  } catch (error) {
    const reason = error && error.message ? error.message : String(error)
    throw new Error('butler kernel failed to start: ' + reason)
  }

  const stdout = collectedText(handle, 'stdout')
  const stderr = collectedText(handle, 'stderr')

  if (deadline.aborted && !(callerSignal !== undefined && callerSignal.aborted)) {
    throw new Error('butler kernel timed out after ' + TIMEOUT_MS + 'ms: ' + argv[2]
      + (stderr === '' ? '' : '\n' + stderr))
  }
  if (callerSignal !== undefined && callerSignal.aborted) {
    throw new Error('butler call cancelled: ' + argv[2])
  }
  if (outcome.exitCode === null) {
    throw new Error('butler kernel terminated by ' + String(outcome.signal) + ': ' + argv[2]
      + (stderr === '' ? '' : '\n' + stderr))
  }
  if (outcome.exitCode !== 0) {
    // 契约：非零退出码时把内核 stderr 原样交给模型。
    throw new Error(stderr !== '' ? stderr : 'butler kernel exited with code ' + String(outcome.exitCode))
  }
  if (stdout.trim() === '') {
    throw new Error('butler kernel produced no stdout (exit 0): ' + argv[2])
  }
  try {
    return JSON.parse(stdout)
  } catch (error) {
    throw new Error('butler kernel returned non-JSON stdout:\n' + stdout
      + (stderr === '' ? '' : '\n--- stderr ---\n' + stderr))
  }
}

// ---- 工具表（与 butler_cli.py 子命令 1:1）--------------------------------

const TOKEN = { type: 'string', description: '访问令牌（匿名可空）' }

function params(properties, required) {
  const schema = { type: 'object', properties, additionalProperties: true }
  if (Array.isArray(required) && required.length > 0) schema.required = [...required]
  return schema
}

const SPECS = [
  {
    name: 'butler_ask',
    description: '向职场管家提问，答案带档案原文引用；无证据时明说，越权信息拒答。',
    parameters: params({
      question: { type: 'string', description: '要问的问题' },
      token: TOKEN,
    }, ['question']),
    required: ['question'],
    argv: (args) => command('ask', args.question, (a) => { flag(a, '--token', args.token) }),
  },
  {
    name: 'butler_profile',
    description: '按分节获取档案。分节键：identity、meta、career_events、skills、certs、education、'
      + 'evidence、workflows（preferences/contact 需授权令牌）；越权时内核返回“存在但需授权”。',
    parameters: params({
      section: { type: 'string', description: '分节键，取值见工具说明' },
      token: TOKEN,
    }, ['section']),
    required: ['section'],
    argv: (args) => command('profile', args.section, (a) => { flag(a, '--token', args.token) }),
  },
  {
    name: 'butler_preferences',
    description: '获取求职偏好（隐私层，需授权令牌）。',
    parameters: params({ token: TOKEN }),
    required: [],
    argv: (args) => command('preferences', undefined, (a) => { flag(a, '--token', args.token) }),
  },
  {
    name: 'butler_reveal',
    description: '匿名→实名揭示（一次性授权令牌，用后作废并留痕）。',
    parameters: params({
      token: { type: 'string', description: '一次性揭示令牌' },
    }, ['token']),
    required: ['token'],
    argv: (args) => command('reveal', undefined, (a) => { flag(a, '--token', args.token) }),
  },
  {
    name: 'butler_verify',
    description: '出示某条主张的登记处签名徽章；无签名的主张一律按自述 ○ 处理。',
    parameters: params({
      claim_id: { type: 'string', description: '主张编号' },
    }, ['claim_id']),
    required: ['claim_id'],
    argv: (args) => command('verify', args.claim_id, () => {}),
  },
  {
    name: 'butler_schedule',
    description: '预约面试（内核当前为存根：记录请求）。',
    parameters: params({
      when: { type: 'string', description: '时间' },
      note: { type: 'string', description: '备注' },
      token: TOKEN,
    }, ['when']),
    required: ['when'],
    argv: (args) => command('schedule', args.when, (a) => {
      flag(a, '--note', args.note)
      flag(a, '--token', args.token)
    }),
  },
  {
    name: 'butler_summary',
    description: '简历概况：经历列表（含 idx）/技能计数/证据总数。',
    parameters: params({}),
    required: [],
    argv: () => command('summary', undefined, () => {}),
  },
  {
    name: 'butler_add_event',
    description: '新增一段经历。hl 为该段职责/成果条目，ev 为证据编号。',
    parameters: params({
      role: { type: 'string', description: '职位' },
      org: { type: 'string', description: '公司/组织' },
      start: { type: 'string', description: '起始时间' },
      end: { type: 'string', description: '结束时间（在职可空）' },
      hl: { type: 'array', items: { type: 'string' }, description: '职责/成果条目' },
      ev: { type: 'array', items: { type: 'string' }, description: '证据编号' },
    }, ['role', 'org', 'start', 'hl']),
    required: ['role', 'org', 'start', 'hl'],
    argv: (args) => command('add-event', undefined, (a) => {
      flag(a, '--role', args.role)
      flag(a, '--org', args.org)
      flag(a, '--start', args.start)
      flag(a, '--end', args.end)
      repeated(a, '--hl', args.hl)
      repeated(a, '--ev', args.ev)
    }),
  },
  {
    name: 'butler_add_highlight',
    description: '给第 idx 段经历追加一条职责/成果（idx 见 butler_summary 的经历列表）。',
    parameters: params({
      idx: { type: 'integer', description: '经历下标' },
      text: { type: 'string', description: '条目文本' },
    }, ['idx', 'text']),
    required: ['idx', 'text'],
    argv: (args) => command('add-highlight', undefined, (a) => {
      flag(a, '--idx', args.idx)
      flag(a, '--text', args.text)
    }),
  },
  {
    name: 'butler_add_skills',
    description: '追加技能（silicon=AI/数据侧，carbon=领域侧）。',
    parameters: params({
      silicon: { type: 'array', items: { type: 'string' }, description: 'AI/数据侧技能' },
      carbon: { type: 'array', items: { type: 'string' }, description: '领域侧技能' },
    }),
    required: [],
    argv: (args) => command('add-skills', undefined, (a) => {
      repeated(a, '--silicon', args.silicon)
      repeated(a, '--carbon', args.carbon)
    }),
  },
  {
    name: 'butler_regen',
    description: '从主副本重新生成简历页 page.html。',
    parameters: params({}),
    required: [],
    argv: () => command('regen', undefined, () => {}),
  },
  {
    name: 'butler_jobs_add',
    description: '记录一个在看的机会（desc 为 JD 原文，用于匹配；note 为个人备注）。',
    parameters: params({
      title: { type: 'string', description: '职位名' },
      company: { type: 'string', description: '公司' },
      source: { type: 'string', description: '来源' },
      desc: { type: 'string', description: 'JD 原文' },
      note: { type: 'string', description: '个人备注' },
    }, ['title', 'company']),
    required: ['title', 'company'],
    argv: (args) => command('jobs-add', undefined, (a) => {
      flag(a, '--title', args.title)
      flag(a, '--company', args.company)
      flag(a, '--source', args.source)
      flag(a, '--desc', args.desc)
      flag(a, '--note', args.note)
    }),
  },
  {
    name: 'butler_jobs',
    description: '列出我在看的全部机会及状态。',
    parameters: params({}),
    required: [],
    argv: () => command('jobs', undefined, () => {}),
  },
  {
    name: 'butler_jobs_status',
    description: '更新机会状态（看机会/已投递/沟通中/面试中/offer/放弃）。',
    parameters: params({
      job_id: { type: 'string', description: '机会编号' },
      status: { type: 'string', description: '新状态' },
    }, ['job_id', 'status']),
    required: ['job_id', 'status'],
    argv: (args) => command('jobs-status', undefined, (a) => {
      flag(a, '--id', args.job_id)
      flag(a, '--status', args.status)
    }),
  },
  {
    name: 'butler_match',
    description: '关键词匹配：该职位 JD vs 我的档案（matched/missing 全列出，人做判断）。',
    parameters: params({
      job_id: { type: 'string', description: '机会编号' },
    }, ['job_id']),
    required: ['job_id'],
    argv: (args) => command('match', undefined, (a) => { flag(a, '--id', args.job_id) }),
  },
]

function assertRequired(spec, args) {
  const missing = []
  for (const key of spec.required) {
    const value = args === undefined || args === null ? undefined : args[key]
    if (value === undefined || value === null || value === '') missing.push(key)
  }
  if (missing.length > 0) {
    throw new Error(spec.name + ' missing required argument(s): ' + missing.join(', ')
      + ' — no kernel process was started.')
  }
}

// ---- 挂载 ---------------------------------------------------------------

export function apply(ctx) {
  for (const spec of SPECS) {
    ctx.tools.register({
      name: spec.name,
      description: spec.description,
      parameters: spec.parameters,
      output: {
        // 内核返回值形状由内核决定；用空 schema 表示“任意无损 JSON”，
        // 与动态插件里 DSL 的 `{ type: 'json' }` 编译结果一致。
        schema: {},
        render(_args, value) {
          return [{ type: 'text', text: JSON.stringify(value, null, 2) }]
        },
      },
      // 与内核 60s 超时同源的协作式预算（略高于内核，让内核先自杀）。
      timeoutMs: TIMEOUT_MS + 5000,
      async execute(args, exec) {
        assertRequired(spec, args)
        return callKernel(ctx, spec.argv(args || {}), exec)
      },
    })
  }
}
