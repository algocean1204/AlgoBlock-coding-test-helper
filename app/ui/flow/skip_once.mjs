// 흐름 시험: '이대로 넘어가기'(블록 칸의 [data-skip], 튜터 말의 [data-act="skip"])와 '끝까지 내 방식으로 쓰기'([data-own], 의자에서는 확인 칸의 [data-own-yes])를
// 빨리 두 번 눌러도 같은 블록의 넘어가기 요청(block_filled, skip)은 한 번만 간다. 한쪽 요청이 끝날 때까지 두 단추가 모두 잠겨 보이고 다른 쪽을 눌러도 보내지 않는다.
// 요청이 실패하면 다시 눌러 보낼 수 있다.
// 쓰는 법: node skip_once.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델은 쓰지 않는다. 문제 상태 응답(/api/state)의 대화·블록을 route가 꾸며 주고, 넘어가기 요청은 붙잡았다가 꾸민 응답으로 답한다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node skip_once.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const PID = 'hash_1_popular_shelf'
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const CODE = 'count = {}\n'
const at = '2026-10-15T00:00:00+09:00'
const PARTS = { block_index: 2, result: '아직 이어지지 않아요.', buttons: ['fill', 'skip'] }
const CHAT = [
  { id: 'm1', role: 'service', text: '첫 질문이에요. 무엇부터 볼까요?', at, block_index: 0, move: 'open' },
  { id: 'm2', role: 'service', text: PARTS.result, at, block_index: 2, move: 'clue', parts: PARTS },
]
const SKIP = '#blocks [data-skip]', OWN = '#blocks [data-own]', SKIPPED = /다음 블록을 열었어요/, OPENED = /남은 블록을 모두 열었어요/
// press: 보내는 단추, ask: 그 앞에 묻는 확인 칸을 여는 단추, lock: 기다리는 동안 잠겨 보일 단추(없으면 press), other: 그동안 눌러도 보내지 않을 다른 단추
const SCENARIOS = {
  block: { way: 'guide', press: SKIP, other: OWN, done: SKIPPED },
  chat: { way: 'guide', press: '#chat-log .msg.tutor[data-msg="m2"] [data-act="skip"]', other: OWN, done: SKIPPED },
  own: { way: 'guide', press: OWN, other: SKIP, done: OPENED },
  'own-ask': { way: 'chair', ask: OWN, press: '#blocks [data-own-yes]', lock: OWN, other: SKIP, done: OPENED },
}
const deferred = () => { let resolve; const promise = new Promise((r) => { resolve = r }); return { promise, resolve } }

const browser = await launch()
let failed = 0

async function flow(which, viewport) {
  const tag = `skip_once-${which}-${viewport.width}x${viewport.height}`
  const cfg = SCENARIOS[which], sel = cfg.press, lock = cfg.lock || sel
  const context = await browser.newContext({ viewport })
  context.setDefaultTimeout(4000)
  const page = await context.newPage()
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problems.push(`console: ${m.text()}`) })
  await page.addInitScript(() => { // 화면이 보낸 넘어가기 요청 수(누른 그 자리에서 센다. 망을 거쳐 오는 순서를 기다리지 않는다)
    window.__skips = 0
    const real = window.fetch
    window.fetch = (path, init) => { if (path === '/api/turn' && JSON.parse((init && init.body) || '{}').skip === true) window.__skips++; return real(path, init) } // 넘어가기와 내 방식 모두
  })
  let gate = deferred(), routed = 0
  await page.route('**/*', async (route) => {
    const req = route.request(), url = new URL(req.url())
    if (url.origin !== new URL(base).origin) {
      if (/^(data|blob|about):/.test(req.url())) return route.continue()
      problems.push(`external: ${req.url()}`)
      return route.abort()
    }
    if (url.pathname === '/api/accounts') { const res = await route.fetch(); return route.fulfill({ response: res, json: { ...(await res.json()), connected: true } }) }
    if (url.pathname === '/api/state') {
      const res = await route.fetch(), json = await res.json()
      const s = json.session
      if (s && s.blocks && s.blocks.length >= 4) { // 3번째 블록이 지금 블록이고, 확인이 통과하지 못해 넘어갈 길이 보인다
        s.blocks = s.blocks.map((b, i) => ({ ...b, name: `시험블록${i + 1}`, ...(i === 2 ? { checked: CODE, verdict: 'N' } : {}) }))
        s.open_count = 3
        s.chair = s.guide = CHAT
        s.followups = []
        json.blocks = { [s.blocks[2].id]: { code: CODE, by: 'me', line: { ok: false, text: PARTS.result } } }
      }
      return route.fulfill({ response: res, json })
    }
    if (url.pathname === '/api/turn') {
      const body = JSON.parse(req.postData() || '{}')
      if (body.event === 'block_filled' && body.skip) {
        routed++
        const how = await gate.promise // 풀 때까지 응답을 붙잡는다
        if (how === 'fail') return route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: { code: 'internal', message: '넘어가지 못했어요.' } }) })
        return route.fulfill({ json: { messages: CHAT, open_count: 3, renamed: [], withdrawn: [], repeated: false, unsure: false } })
      }
      problems.push(`모델 요청: ${url.pathname} ${body.event}`)
      return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' })
    }
    if (/^\/api\/(followup|fill|explain|feedback|debug)$/.test(url.pathname)) { problems.push(`모델 요청: ${url.pathname}`); return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }) }
    return route.continue()
  })
  const release = (how) => { const g = gate; gate = deferred(); g.resolve(how) }
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n').slice(0, 3).join(' | ')}`) } }
  const r = await context.request.post(`${base}/api/reset`, { data: { id: PID } })
  if (!r.ok()) problems.push(`reset ${r.status()}`)
  await page.goto(`${base}/#/p/${PID}`)
  await need('문제 제목이 그려진다', () => page.waitForFunction(() => document.getElementById('p-title')?.textContent.trim().length > 0, null, { timeout: 15000 }))
  await need('튜터 말과 두 단추가 보인다', async () => {
    if (await page.locator('#problem-peek').isVisible()) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() }
    await page.locator(`#way-tabs [data-way="${cfg.way}"]`).click()
    for (const one of [cfg.ask || sel, cfg.other]) await page.locator(one).waitFor({ state: 'visible', timeout: 10000 })
  })
  const sent = () => page.evaluate(() => window.__skips)
  const locked = (sel, yes) => page.waitForFunction(([sel, yes]) => { const el = document.querySelector(sel); return !!el && (el.disabled || el.getAttribute('aria-disabled') === 'true') === yes }, [sel, yes])
  const ask = async () => { if (cfg.ask) { await page.locator(cfg.ask).click(); await page.locator(sel).waitFor({ state: 'visible' }) } } // 의자: 묻는 칸을 먼저 연다(여기서는 아직 보내지 않는다)

  await need('빨리 두 번 누르면 넘어가기 요청은 하나다', async () => {
    await ask()
    if ((await sent()) !== 0) throw new Error(`묻기 전에 넘어가기 요청 ${await sent()}회`)
    await page.locator(sel).evaluate((el) => { el.click(); el.click() })
    const n = await sent()
    if (n !== 1) throw new Error(`넘어가기 요청 ${n}회`)
  })
  await need('요청이 끝나기 전에는 어느 단추를 다시 눌러도 보내지 않고, 두 단추가 잠겨 보인다', async () => {
    await page.locator(lock).evaluate((el) => el.click())
    await page.locator(cfg.other).evaluate((el) => el.click())
    if ((await sent()) !== 1) throw new Error(`넘어가기 요청 ${await sent()}회`)
    await locked(lock, true)
    await locked(cfg.other, true)
  })
  await need('요청이 실패하면 단추가 풀리고 다시 누르면 한 번 더 보낸다', async () => {
    release('fail')
    await locked(lock, false)
    await locked(cfg.other, false)
    await ask()
    await page.locator(sel).click()
    if ((await sent()) !== 2) throw new Error(`넘어가기 요청 ${await sent()}회`)
  })
  await need('두 번째 요청이 끝나면 그 결과를 알리고, 서버가 받은 요청도 둘이다', async () => {
    release('ok')
    await page.waitForFunction((done) => new RegExp(done).test(document.getElementById('status').textContent), cfg.done.source)
    if (routed !== 2) throw new Error(`서버로 간 넘어가기 요청 ${routed}회`)
  })
  release('ok') // 실패한 걸음에서 붙잡힌 요청이 남지 않게
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `${tag}.png`) }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.unrouteAll({ behavior: 'ignoreErrors' })
  await context.close()
}

for (const viewport of VIEWPORTS) for (const which of Object.keys(SCENARIOS)) await flow(which, viewport)
await browser.close()
process.exit(failed ? 1 : 0)
