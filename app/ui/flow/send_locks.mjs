// 흐름 시험: 보내기와 잠금. Enter로 보내고(조합 중 Enter 포함), 보낸 말이 바로 올라가고, AI가 답하는 중에도 실행·제출이 되고,
// 튜터 답이 와도 블록 칸 커서가 남고, 준비 중 폴링이 가볍고, 개발 표시에서 반응 시간이 남는다.
// 쓰는 법: node send_locks.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델은 쓰지 않는다. 보낸 말·디버그·해설 같은 AI 요청은 화면이 부르는 순간 route가 받아 붙잡거나(hold) 꾸민 응답으로 답한다.
// 정한 이름: 대화 칸 #say(보내기 #send), 디버그 칸 #debug-say, 상태 응답의 준비 표시는 POST /api/prep {id} → {preparing, checking}(1KB 이하),
//   개발 표시는 /api/accounts의 dev가 참일 때 window.__ab.perf = { press_to_paint_ms, send_to_clear_ms, tab_to_change_ms, rerender_ms }.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node send_locks.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const problem = builtin.find((p) => p.language === 'python' && p.ready && p.ready.plan && p.ready.plan.blocks.length > 1 && p.solutions && p.solutions.python)
// 어떤 기본 문제에서도 돌아가는 틀린 코드: 풀이의 첫 줄(함수 머리)만 두고 아무것도 돌려주지 않는다
const WRONG = `${problem.solutions.python.split('\n')[0]}\n    return None\n`
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const deferred = () => { let resolve; const promise = new Promise((r) => { resolve = r }); return { promise, resolve } }

const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

// 요청 판별
const isMessage = (q) => q.path === '/api/turn' && q.body.event === 'message'
const isStart = (q) => q.path === '/api/turn' && q.body.event === 'start'
const isDebug = (q) => q.path === '/api/debug'
const isRun = (q) => q.path === '/api/run'
const isSubmit = (q) => q.path === '/api/submit'
const isState = (q) => q.path === '/api/state'
const isPrep = (q) => q.path === '/api/prep'
const FAIL = { status: 502, json: { detail: { code: 'llm_timeout', message: '모델이 답하지 않았어요' } } }

/** 한 걸음(흐름 × 뷰포트)을 새 문맥·새 화면에서 돌린다. 한 걸음이 실패하면 뒤 걸음은 기다리지 않는다. */
async function flow(name, viewport, steps, opts = {}) {
  const tag = `${name}-${viewport.width}x${viewport.height}`
  const context = await browser.newContext({ viewport })
  context.setDefaultTimeout(4000) // 앱이 아닌 화면에서 한 걸음마다 오래 기다리지 않게
  const page = await context.newPage()
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problems.push(`console: ${m.text()}`) })
  await page.addInitScript(() => {
    window.__long = 0 // 50ms 넘는 긴 작업 수(시험이 따로 센다)
    try { new PerformanceObserver((l) => { window.__long += l.getEntries().length }).observe({ type: 'longtask', buffered: true }) } catch {}
    window.__sa = 0 // '다시 시작' 단추가 보인 횟수
    new MutationObserver(() => { const el = document.getElementById('start-again'); if (el && el.getClientRects().length) window.__sa++ }).observe(document, { subtree: true, childList: true, attributes: true })
  })
  const t = { page, seen: [], rules: [], connected: true, dev: !!opts.dev, stateDelay: opts.stateDelay || 0, mutate: null, prepOn: false, need: null }
  t.count = (pred) => t.seen.filter(pred).length
  t.texts = () => t.seen.filter(isMessage).map((q) => q.body.text)
  /** 처음 맞는 요청 하나를 붙잡는다. release('ok'|'fail'|'continue'|{json}) 로 풀면 그 응답으로 끝난다. 붙잡힌 동안 같은 종류의 다음 요청은 막지 않는다. */
  t.hold = (pred) => {
    const gate = deferred()
    let taken = false
    t.rules.unshift({ pred, handler: async (route, q) => {
      if (taken) return reply(route, q, 'default')
      taken = true
      t.held = q
      return reply(route, q, await gate.promise)
    } })
    return { release: gate.resolve }
  }
  const reply = async (route, q, how) => {
    if (how === 'continue') return route.continue()
    if (how === 'fail') return route.fulfill({ status: FAIL.status, contentType: 'application/json', body: JSON.stringify(FAIL.json) })
    if (how && how.json) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(how.json) })
    if (how === 'ok' || (how === 'default' && isMessage(q))) return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    return route.continue()
  }
  await page.route('**/*', async (route) => {
    const req = route.request(), url = new URL(req.url())
    if (url.origin !== new URL(base).origin) {
      if (/^(data|blob|about):/.test(req.url())) return route.continue()
      problems.push(`external: ${req.url()}`)
      return route.abort()
    }
    if (/perf/i.test(url.pathname) && url.pathname.startsWith('/api/')) problems.push(`성능 값을 서버로 보냈다: ${url.pathname}`)
    if (!url.pathname.startsWith('/api/')) return route.continue()
    let body = {}
    try { body = JSON.parse(req.postData() || '{}') } catch {}
    const q = { path: url.pathname, method: req.method(), body, t: Date.now() }
    t.seen.push(q)
    if (q.path === '/api/accounts') {
      const res = await route.fetch()
      return route.fulfill({ response: res, json: { ...(await res.json()), connected: t.connected, dev: t.dev } })
    }
    if (isState(q)) {
      if (t.stateDelay) await sleep(t.stateDelay)
      const res = await route.fetch()
      let json = await res.json()
      if (t.prepOn) json = { ...json, problem: { ...json.problem, preparing: true } }
      if (t.mutate) json = t.mutate(json) || json
      return route.fulfill({ response: res, json })
    }
    if (isPrep(q) && opts.fakePrep) {
      const on = t.prepOn
      if (++t.prepPolls >= 2) t.prepOn = false
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: problem.id, preparing: on, checking: false }) })
    }
    const rule = t.rules.find((r) => r.pred(q))
    if (rule) return rule.handler(route, q)
    return reply(route, q, 'default')
  })
  t.prepPolls = 0
  let stuck = false
  t.need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  try {
    const r = await context.request.post(`${base}/api/reset`, { data: { id: problem.id }, timeout: 30000 }) // 준비 요청: 화면을 기다리는 4초 기본값과 따로(느린 러너)
    if (!r.ok()) problems.push(`reset ${r.status()}`)
  } catch (e) { problems.push(`reset: ${String(e.message).split('\n')[0]}`) }
  if (opts.prepOn) t.prepOn = true
  await page.goto(`${base}/#/p/${problem.id}`)
  Object.assign(t, {
    blocks: () => page.locator('#blocks > li'),
    current: () => page.locator('#blocks > li.block[aria-current="step"]'),
    pick: async (way) => {
      if (await page.locator('#problem-peek').isVisible()) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() }
      await page.locator(`#way-tabs [data-way="${way}"]`).click()
      await page.locator('#chat-log .msg.tutor').first().waitFor({ state: 'visible', timeout: 10000 })
    },
    value: (id) => page.locator(`#${id}`).inputValue(),
    fire: (id, type, init) => page.evaluate(([id, type, init]) => {
      const el = document.getElementById(id)
      const e = type.startsWith('composition') ? new CompositionEvent(type, { bubbles: true, data: init.data || '' }) : new KeyboardEvent(type, { key: 'Enter', code: 'Enter', bubbles: true, cancelable: true, ...init })
      el.dispatchEvent(e)
      return e.defaultPrevented
    }, [id, type, init || {}]),
    setValue: (id, v) => page.evaluate(([id, v]) => { const el = document.getElementById(id); el.focus(); el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })) }, [id, v]),
    perf: () => page.evaluate(() => (window.__ab && window.__ab.perf ? { ...window.__ab.perf } : null)),
    direct: async () => { await page.evaluate(() => { setCodeTab('direct', 'quiet'); render() }); await page.locator('#code').waitFor({ state: 'visible', timeout: 3000 }) }, // 블록이 비어 있으면 탭 단추는 먼저 경고하므로 같은 길의 함수를 부른다
    open: async (sel) => { if (await page.locator(sel).evaluate((el) => el.disabled || el.getAttribute('aria-disabled') === 'true')) throw new Error(`${sel}가 잠겨 있다`) },
    wrongRun: async () => { await t.direct(); await page.locator('#code').fill(WRONG); await t.open('#run'); await page.locator('#run').click(); await page.waitForFunction(() => document.querySelector('#result .verdict'), null, { timeout: 15000 }) },
  })
  await steps(t)
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `send_locks-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.unrouteAll({ behavior: 'ignoreErrors' }) // 끝난 뒤 늦게 오는 응답이 닫힌 화면에서 던지지 않게
  await context.close()
}

for (const viewport of VIEWPORTS) {
  // ── 1. 대화 칸: Enter로 보내고 Shift+Enter는 줄바꿈 ──
  await flow('enter-say', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('Shift+Enter는 줄을 바꾸고 보내지 않는다', async () => {
      await page.locator('#say').click()
      await page.keyboard.type('첫줄')
      await page.keyboard.press('Shift+Enter')
      await page.keyboard.type('둘째줄')
      await sleep(300)
      if ((await t.value('say')) !== '첫줄\n둘째줄') throw new Error(`값 ${JSON.stringify(await t.value('say'))}`)
      if (t.count(isMessage)) throw new Error('Shift+Enter가 보냈다')
    })
    await need('Enter는 한 번에 보내고 칸이 비고 개행이 남지 않는다', async () => {
      await page.locator('#say').fill('안녕')
      await page.locator('#say').press('Enter')
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 2000 })
      await sleep(300)
      if (t.texts().join('|') !== '안녕') throw new Error(`보낸 글 ${JSON.stringify(t.texts())}`)
    })
    await need('빈 칸에서 Enter는 보내지 않는다', async () => {
      const before = t.count(isMessage)
      await page.locator('#say').fill('  ')
      await page.locator('#say').press('Enter')
      await sleep(300)
      if (t.count(isMessage) !== before) throw new Error('빈 글을 보냈다')
    })
    await need('보내기 단추 클릭도 그대로 보낸다', async () => {
      await page.locator('#say').fill('단추로')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 2000 })
      await sleep(300)
      if (t.texts().pop() !== '단추로') throw new Error(`보낸 글 ${JSON.stringify(t.texts())}`)
    })
  })

  // ── 2. 한글 조합 중 Enter: 조합 중에는 보내지 않고, 확정 Enter 한 번이면 마지막 글자까지 정확히 한 번 ──
  await flow('enter-compose', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    const run = async (label, steps, sends, value) => need(label, async () => {
      const base0 = t.count(isMessage)
      await page.locator('#say').fill('')
      for (const [kind, a, b] of steps) {
        if (kind === 'val') await t.setValue('say', a)
        else if (kind === 'cs') await t.fire('say', 'compositionstart')
        else if (kind === 'ce') await t.fire('say', 'compositionend', { data: a })
        else if (kind === 'key') await t.fire('say', 'keydown', a)
        else if (kind === 'wait') await sleep(a)
        else if (kind === 'none') { if (t.count(isMessage) !== base0) throw new Error('조합이 끝나기 전에 보냈다') }
        await sleep(15)
      }
      await sleep(400)
      const got = t.texts().slice(base0)
      if (got.join('|') !== sends.join('|')) throw new Error(`보낸 글 ${JSON.stringify(got)}, 기대 ${JSON.stringify(sends)}`)
      if (value !== undefined && (await t.value('say')) !== value) throw new Error(`칸 ${JSON.stringify(await t.value('say'))}, 기대 ${JSON.stringify(value)}`)
    })
    const C = { isComposing: true, keyCode: 229 }
    await run('조합 중 Enter 뒤 확정되면 마지막 글자까지 한 번 보낸다(Chromium 순서)', [['val', '안녕하세'], ['cs'], ['key', C], ['none'], ['val', '안녕하세요'], ['ce', '요']], ['안녕하세요'], '')
    await run('확정 뒤에 오는 keyCode 229 Enter도 한 번만 보낸다(WebKit 순서)', [['val', '안녕하세'], ['cs'], ['val', '안녕하세요'], ['ce', '요'], ['key', { isComposing: false, keyCode: 229 }]], ['안녕하세요'], '')
    await run('한 번 누른 Enter가 두 번 오면(조합 중, 확정 뒤) 한 번만 보낸다', [['val', '안녕하세'], ['cs'], ['key', C], ['val', '안녕하세요'], ['ce', '요'], ['key', { isComposing: false, keyCode: 13 }]], ['안녕하세요'], '')
    await run('조합 중 Shift+Enter는 보내지 않고 글을 그대로 둔다', [['val', '안녕하세'], ['cs'], ['key', { ...C, shiftKey: true }], ['val', '안녕하세요'], ['ce', '요'], ['wait', 300]], [], '안녕하세요')
    await run('조합만 하고 Enter가 없으면 보내지 않는다', [['val', '안녕'], ['cs'], ['val', '안녕하'], ['wait', 300]], [], '안녕하')
    await need('조합 뒤의 보통 Enter는 다시 보낸다(막힌 채로 남지 않는다)', async () => {
      await page.locator('#say').fill('')
      await page.locator('#say').fill('다음')
      await page.locator('#say').press('Enter')
      await sleep(400)
      if (t.texts().pop() !== '다음') throw new Error(`보낸 글 ${JSON.stringify(t.texts())}`)
    })
  })

  // ── 3. 코드 칸·내 입력 칸·문제 글 칸은 Ctrl/Cmd+Enter 그대로(Enter는 줄바꿈) ──
  await flow('enter-other', viewport, async (t) => {
    const { need, page } = t
    await need('코드 칸: Enter는 줄바꿈, Ctrl+Enter는 제출', async () => {
      await t.direct()
      await page.locator('#code').fill('x = 1')
      await page.locator('#code').press('End')
      await page.locator('#code').press('Enter')
      await sleep(200)
      if (!(await t.value('code')).includes('\n') || t.count(isSubmit)) throw new Error('Enter가 줄을 바꾸지 않았거나 제출했다')
      t.rules.unshift({ pred: isSubmit, handler: async (route) => { await sleep(1800); return route.continue() } }) // 채점이 느려도 끝을 기다리는지 본다
      await page.locator('#code').press('Control+Enter')
      await page.waitForFunction(() => { const run = document.getElementById('run'); return !run.disabled && run.getAttribute('aria-disabled') !== 'true' && document.querySelector('#result .verdict') }, null, { timeout: 15000 }) // 진행 문구(.note)가 아니라 결과가 나오고 실행 줄이 풀릴 때까지
      if (t.count(isSubmit) !== 1) throw new Error(`제출 ${t.count(isSubmit)}회`)
    })
    await need('내 입력 칸: Enter는 줄바꿈, Ctrl+Enter는 실행', async () => {
      await page.locator('#run-own summary').click()
      await page.locator('#run-input').fill('1')
      await page.locator('#run-input').press('Enter')
      await sleep(200)
      if (!(await t.value('run-input')).includes('\n') || t.count(isRun)) throw new Error('Enter가 줄을 바꾸지 않았거나 실행했다')
      await page.locator('#run-input').press('Control+Enter')
      await page.waitForFunction(() => true)
      await sleep(500)
      if (t.count(isRun) !== 1) throw new Error(`실행 ${t.count(isRun)}회`)
    })
    await need('문제 글 칸: Enter는 줄바꿈이고 등록하지 않는다', async () => {
      await page.goto(`${base}/#/new`)
      await page.locator('#new-text').waitFor({ state: 'visible', timeout: 5000 })
      await page.locator('#new-text').fill('문제')
      await page.locator('#new-text').press('End')
      await page.locator('#new-text').press('Enter')
      await sleep(300)
      if (!(await page.locator('#new-text').inputValue()).includes('\n')) throw new Error('줄이 바뀌지 않았다')
      if (t.seen.some((q) => /^\/api\/problems\/(add|register|new|create)/.test(q.path) || (q.path === '/api/problems' && q.method === 'POST' && q.body.text))) throw new Error('Enter가 등록했다')
    })
  })

  // ── 4. 낙관적 표시: 보내면 곧바로 칸이 비고 내 말이 올라가며, 실패하면 글이 돌아온다 ──
  await flow('optimistic-say', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    let gate
    await need('보내면 응답 전에 칸이 비고 내 말이 대화에 올라간다', async () => {
      gate = t.hold(isMessage)
      await page.locator('#say').fill('내 생각이에요')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '' && [...document.querySelectorAll('#chat-log .msg.me')].some((m) => m.textContent.includes('내 생각이에요')), null, { timeout: 1500 })
      if (!t.held) throw new Error('응답을 붙잡기 전에 확인했어야 한다')
    })
    await need('성공하면 칸은 빈 채로 남는다', async () => { gate.release('ok'); await sleep(500); if ((await t.value('say')) !== '') throw new Error('칸이 다시 찼다') })
    await need('실패하면 글이 칸에 돌아온다', async () => {
      t.held = null
      gate = t.hold(isMessage)
      await page.locator('#say').fill('실패할 글')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 1500 })
      gate.release('fail')
      await page.waitForFunction(() => document.getElementById('say').value === '실패할 글', null, { timeout: 4000 })
    })
    await need('실패하는 사이 새로 쓴 글이 있으면 둘 다 남고 되돌린 글은 한 번만 있다', async () => {
      t.held = null
      await page.locator('#say').fill('')
      gate = t.hold(isMessage)
      await page.locator('#say').fill('보낸 글')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 1500 })
      await page.locator('#say').fill('그사이 쓴 글')
      gate.release('fail')
      await page.waitForFunction(() => document.getElementById('say').value.includes('보낸 글'), null, { timeout: 4000 })
      const v = await t.value('say')
      if (!v.includes('그사이 쓴 글') || v.split('보낸 글').length !== 2) throw new Error(`값 ${JSON.stringify(v)}`)
    })
  })

  // ── 5. 디버그 답도 같다 ──
  await flow('optimistic-debug', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('틀린 코드를 돌려 ‘틀린 곳 같이 찾기’를 연다', async () => {
      t.rules.unshift({ pred: (q) => isDebug(q) && !q.body.text, handler: (route, q) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: '어디서 값이 사라질까요?', passed: false, line: null }) }) })
      await t.wrongRun()
      await page.locator('#debug-start').click()
      await page.locator('#debug-say').waitFor({ state: 'visible', timeout: 5000 })
    })
    let gate
    await need('Enter로 보내면 응답 전에 칸이 비고 내 말이 올라간다', async () => {
      gate = t.hold((q) => isDebug(q) && q.body.text)
      await page.locator('#debug-say').fill('반환값이 없어요')
      await page.locator('#debug-send').click()
      await page.waitForFunction(() => document.getElementById('debug-say').value === '' && [...document.querySelectorAll('#debug-log .msg.me')].some((m) => m.textContent.includes('반환값이 없어요')), null, { timeout: 1500 })
    })
    await need('실패하면 글이 칸에 돌아오고 그사이 쓴 글은 함께 남는다', async () => {
      await page.locator('#debug-say').fill('그사이')
      gate.release('fail')
      await page.waitForFunction(() => document.getElementById('debug-say').value.includes('반환값이 없어요'), null, { timeout: 4000 })
      const v = await t.value('debug-say')
      if (!v.includes('그사이') || v.split('반환값이 없어요').length !== 2) throw new Error(`값 ${JSON.stringify(v)}`)
    })
    await need('Shift+Enter는 디버그 칸에서도 줄을 바꾸고 보내지 않는다', async () => {
      const before = t.count((q) => isDebug(q) && q.body.text)
      await page.locator('#debug-say').fill('')
      await page.locator('#debug-say').click()
      await page.keyboard.type('가')
      await page.keyboard.press('Shift+Enter')
      await page.keyboard.type('나')
      await sleep(300)
      if ((await t.value('debug-say')) !== '가\n나' || t.count((q) => isDebug(q) && q.body.text) !== before) throw new Error('줄바꿈이 아니다')
    })
    await need('조합 중 Enter 뒤 확정되면 디버그 칸도 한 번만 보낸다', async () => {
      t.rules.unshift({ pred: (q) => isDebug(q) && q.body.text, handler: (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: '그다음은요?', passed: false, line: null }) }) }) // 모델을 부르지 않게 꾸민 응답
      const before = t.count((q) => isDebug(q) && q.body.text)
      await page.locator('#debug-say').fill('')
      await t.setValue('debug-say', '안녕하세'); await t.fire('debug-say', 'compositionstart')
      await t.fire('debug-say', 'keydown', { isComposing: true, keyCode: 229 }); await sleep(30)
      if (t.count((q) => isDebug(q) && q.body.text) !== before) throw new Error('조합이 끝나기 전에 보냈다')
      await t.setValue('debug-say', '안녕하세요'); await t.fire('debug-say', 'compositionend', { data: '요' }); await sleep(500)
      const sent = t.seen.filter((q) => isDebug(q) && q.body.text).slice(before).map((q) => q.body.text)
      if (sent.join('|') !== '안녕하세요') throw new Error(`보낸 글 ${JSON.stringify(sent)}`)
    })
  })

  // ── 6. 잠금 나누기 ──
  await flow('locks-ai-then-run', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    let gate
    await need('대화에 답하는 중에도 예시 실행이 돼서 결과가 나온다', async () => {
      gate = t.hold(isMessage)
      await page.locator('#say').fill('답이 오는 중')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.querySelector('#chat-log .msg.tutor.pending'), null, { timeout: 2000 })
      await t.wrongRun()
      if (!t.held || t.count(isRun) !== 1) throw new Error('붙잡힌 채 실행이 되지 않았다')
    })
    await need('같은 AI 줄 안에서는 겹치지 않는다(대화 중 둘째 보내기는 나가지 않고 글이 남는다)', async () => {
      await page.locator('#say').fill('둘째 말')
      await page.locator('#send').click({ force: true })
      await sleep(400)
      if (t.count(isMessage) !== 1) throw new Error(`보내기 ${t.count(isMessage)}회`)
      if ((await t.value('say')) !== '둘째 말') throw new Error('기다리는 사이 쓴 글이 사라졌다')
    })
    await need('답하는 중에도 제출이 된다', async () => {
      await t.open('#submit')
      await page.locator('#submit').click()
      await page.waitForFunction(() => /채점|제출|통과|틀려|아직/.test(document.querySelector('#result')?.textContent || ''), null, { timeout: 15000 })
      if (t.count(isSubmit) !== 1) throw new Error(`제출 ${t.count(isSubmit)}회`)
    })
    await need('답이 오면 대화 줄이 풀린다', async () => {
      gate.release('ok')
      await page.waitForFunction(() => !document.querySelector('#chat-log .msg.tutor.pending'), null, { timeout: 4000 })
    })
  })
  await flow('locks-run-then-ai', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('코드를 실행하는 중에도 대화를 보낼 수 있다', async () => {
      const slow = deferred()
      t.rules.unshift({ pred: isRun, handler: async (route) => { await slow.promise; return route.continue() } })
      await t.direct()
      await page.locator('#code').fill(WRONG)
      await page.locator('#run').click()
      await sleep(300)
      if (t.count(isRun) !== 1) throw new Error('실행 요청이 나가지 않았다')
      await page.locator('#say').fill('실행 중에 보낸 말')
      await t.open('#send')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 1500 })
      await sleep(300)
      if (t.texts().join('|') !== '실행 중에 보낸 말') throw new Error(`보낸 글 ${JSON.stringify(t.texts())}`)
      if (await page.locator('#result .verdict').count()) throw new Error('실행이 끝나기 전에 결과가 나왔다(시험 준비가 틀림)')
      t.slow = slow
    })
    await need('실행 줄 안에서는 겹치지 않는다(실행 중 한 번 더 눌러도 요청은 하나)', async () => {
      await page.locator('#run').click({ force: true })
      await sleep(300)
      if (t.count(isRun) !== 1) throw new Error(`실행 ${t.count(isRun)}회`)
      t.slow.resolve()
      await page.waitForFunction(() => document.querySelector('#result .verdict'), null, { timeout: 15000 })
    })
  })
  await flow('locks-start-and-debug', viewport, async (t) => {
    const { need, page } = t
    await need('튜터가 시작하는 중에도 예시 실행이 된다', async () => {
      const gate = t.hold(isStart)
      if (await page.locator('#problem-peek').isVisible()) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() }
      await page.locator('#way-tabs [data-way="chair"]').click()
      await page.waitForFunction(() => document.querySelector('#chat-log .msg.tutor.pending, #tutor-note .dots'), null, { timeout: 3000 })
      await t.wrongRun()
      gate.release('continue')
      await page.locator('#chat-log .msg.tutor:not(.pending)').first().waitFor({ state: 'visible', timeout: 10000 })
    })
    await need('디버그 답을 기다리는 중에도 예시 실행이 된다', async () => {
      t.rules.unshift({ pred: (q) => isDebug(q) && !q.body.text, handler: (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: '어디서 값이 사라질까요?', passed: false, line: null }) }) })
      await page.locator('#debug-start').click()
      await page.locator('#debug-say').waitFor({ state: 'visible', timeout: 5000 })
      const gate = t.hold((q) => isDebug(q) && q.body.text)
      await page.locator('#debug-say').fill('모르겠어요')
      await page.locator('#debug-send').click()
      await page.waitForFunction(() => document.querySelector('#debug-log .msg.tutor.pending'), null, { timeout: 2000 })
      const runs = t.count(isRun)
      await t.open('#run')
      await page.locator('#run').click()
      await sleep(1500)
      if (t.count(isRun) !== runs + 1) throw new Error('디버그 답을 기다리는 중 실행이 나가지 않았다')
      gate.release('fail')
    })
  })

  // ── 6b. 디버그 답을 기다리는 사이 제출이 통과하면 늦게 온 디버그 응답이 통과 결과와 표시를 덮지 않는다 ──
  await flow('debug-late-answer', viewport, async (t) => {
    const { need, page } = t
    let wrongResult
    await need('틀린 코드의 채점 결과(실패)를 얻어 둔다', async () => {
      const r = await page.request.post(`${base}/api/run`, { data: { id: problem.id, code: WRONG }, timeout: 30000 }) // 준비 요청(채점은 느린 러너에서 4초를 넘을 수 있다)
      wrongResult = await r.json()
      if (wrongResult.ok) throw new Error('틀린 코드가 통과했다')
    })
    await need('튜터의 질문으로를 시작해 틀린 곳 찾기를 연다', async () => {
      await t.pick('chair')
      t.rules.unshift({ pred: (q) => isDebug(q) && !q.body.text, handler: (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: '어디서 값이 사라질까요?', passed: false, line: null }) }) })
      await t.wrongRun()
      await page.locator('#debug-start').click()
      await page.locator('#debug-say').waitFor({ state: 'visible', timeout: 5000 })
      await page.waitForFunction(() => document.querySelector('#debug-log .msg.tutor:not(.pending)') && !document.querySelector('#debug-log .msg.tutor.pending'), null, { timeout: 5000 }) // 첫 질문이 와서 기다림이 끝날 때까지
    })
    let gate
    await need('디버그 답을 붙잡아 둔 채 정답을 제출하면 통과한다', async () => {
      gate = t.hold((q) => isDebug(q) && q.body.text)
      await page.locator('#debug-say').fill('모르겠어요')
      await t.open('#debug-send')
      await page.locator('#debug-send').click()
      await page.waitForFunction(() => document.querySelector('#debug-log .msg.tutor.pending'), null, { timeout: 2000 })
      await page.locator('#code').fill(problem.solutions.python)
      await t.open('#submit')
      await page.locator('#submit').click()
      await page.waitForFunction(() => document.querySelector('#result .verdict.pass') && document.querySelector('#debug-log .note.ok'), null, { timeout: 15000 })
    })
    await need('늦게 온 디버그 응답(채점 실패·통과 아님)이 풀려도 결과 칸은 통과로 남는다', async () => {
      gate.release({ json: { message: '아직 틀려요', passed: false, line: 1, judged: wrongResult } })
      await page.waitForFunction(() => !document.querySelector('#debug-log .msg.tutor.pending'), null, { timeout: 4000 })
      await sleep(500)
      if (!(await page.locator('#result .verdict.pass').count()) || await page.locator('#result .verdict.fail').count()) throw new Error('결과 칸이 통과가 아니다')
    })
    await need('디버그 통과 표시가 남고 입력 칸은 닫힌 채다', async () => {
      if (!(await page.locator('#debug-log .note.ok').count())) throw new Error('통과 표시가 사라졌다')
      if (!(await page.locator('#debug-composer').evaluate((el) => el.hidden))) throw new Error('입력 칸이 다시 열렸다')
    })
  })

  // ── 7. 다시 그리기: 튜터 답이 와도 블록 칸의 커서가 남는다 / 같은 HTML이면 다시 그리지 않는다 ──
  await flow('cursor-kept', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('블록 칸에 쓰고 일부를 선택해 둔다', async () => {
      const box = t.current().locator('textarea.codey')
      await box.fill('abcdef')
      await box.evaluate((el) => { el.focus(); el.setSelectionRange(2, 4) })
    })
    let gate
    await need('답을 기다리는 사이 블록 칸에 초점을 두고 튜터 답이 새로 온다', async () => {
      gate = t.hold(isMessage)
      await page.locator('#say').fill('말')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.querySelector('#chat-log .msg.tutor.pending'), null, { timeout: 2000 })
      await t.current().locator('textarea.codey').evaluate((el) => { el.focus(); el.setSelectionRange(2, 4) })
      t.mutate = (json) => { // 서버가 튜터 말을 하나 더 한 것처럼 꾸민다
        const chat = json.session.chair
        if (chat && chat.length) { const { parts, ...last } = chat[chat.length - 1]; chat.push({ ...last, id: `answer-${chat.length}`, text: '새 튜터 말이에요' }) } // 칸(parts)이 있는 말은 칸으로 그려져, 글만 바꾼 말에는 칸을 떼어 글로 그리게 한다
        return json
      }
      gate.release('ok')
      await page.waitForFunction(() => [...document.querySelectorAll('#chat-log .msg.tutor')].some((m) => m.textContent.includes('새 튜터 말이에요')), null, { timeout: 5000 })
    })
    await need('커서가 같은 블록 칸에 같은 선택 범위로 남는다', async () => {
      const got = await page.evaluate(() => { const a = document.activeElement; return { tag: a.tagName, cls: a.className, block: a.dataset && a.dataset.block, value: a.value, s: a.selectionStart, e: a.selectionEnd } })
      if (got.tag !== 'TEXTAREA' || !got.block || got.value !== 'abcdef' || got.s !== 2 || got.e !== 4) throw new Error(JSON.stringify(got))
    })
  })
  await flow('redraw-same-html', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 시작한다', () => t.pick('chair'))
    await need('내용이 같으면 블록 칸과 대화를 다시 그리지 않는다(마킹한 노드가 그대로)', async () => {
      await page.evaluate(() => { render(); for (const el of document.querySelectorAll('#blocks > li, #chat-log .msg')) el.__kept = true })
      const n = await page.evaluate(() => document.querySelectorAll('#blocks > li, #chat-log .msg').length)
      if (n < 2) throw new Error('마킹할 노드가 없다')
      await page.evaluate(() => { render(); render() })
      const lost = await page.evaluate(() => [...document.querySelectorAll('#blocks > li, #chat-log .msg')].filter((el) => !el.__kept).length)
      if (lost) throw new Error(`다시 만들어진 노드 ${lost}개`)
    })
    await need('내용이 같은 상태 응답이 와도 블록 칸 노드가 그대로다', async () => {
      await page.evaluate(() => { for (const el of document.querySelectorAll('#blocks > li')) el.__kept = true })
      await page.evaluate(() => loadState())
      await sleep(600)
      const lost = await page.evaluate(() => [...document.querySelectorAll('#blocks > li')].filter((el) => !el.__kept).length)
      if (lost) throw new Error(`다시 만들어진 블록 ${lost}개`)
    })
  })
}

// ── 8. 준비 중 폴링: 가벼운 요청만 보내고, 값이 바뀔 때만 전체 상태를 한 번 받는다 ──
for (const viewport of VIEWPORTS.slice(0, 1)) {
  await flow('prep-poll', viewport, async (t) => {
    const { need, page } = t
    let baseState = 0
    await need('준비 중으로 열리면 처음 상태 요청 뒤에는 /api/prep만 부른다', async () => {
      await page.locator('#way-tabs').waitFor({ state: 'visible', timeout: 5000 })
      await sleep(1000)
      baseState = t.count(isState)
      if (!baseState) throw new Error('상태 요청이 없다')
      await page.waitForFunction(() => true)
      const deadline = Date.now() + 20000
      while (t.prepPolls < 2 && Date.now() < deadline) await sleep(200)
      if (t.prepPolls < 2) throw new Error(`준비 폴링 ${t.prepPolls}회(/api/prep을 부르지 않는다)`)
      if (t.count(isState) !== baseState) throw new Error(`준비 중에 전체 상태를 ${t.count(isState) - baseState}번 더 받았다`)
    })
    await need('준비가 끝났다고 바뀌면 전체 상태를 한 번만 받고 폴링을 멈춘다', async () => {
      const deadline = Date.now() + 15000
      while (t.count(isState) === baseState && Date.now() < deadline) await sleep(200)
      if (t.count(isState) !== baseState + 1) throw new Error(`상태 요청 ${t.count(isState) - baseState}번 늘었다`)
      const polls = t.count(isPrep)
      await sleep(5000) // 폴링 간격(3초)의 1.5배 이상
      if (t.count(isPrep) !== polls || t.count(isState) !== baseState + 1) throw new Error('끝난 뒤에도 요청이 계속 나간다')
    })
    await need('실제 /api/prep은 1KB 이하의 가벼운 응답이다', async () => {
      const r = await page.request.post(`${base}/api/prep`, { data: { id: problem.id }, timeout: 30000 }) // 응답 크기를 본다(시간은 보지 않는다)
      if (!r.ok()) throw new Error(`상태 ${r.status()}`)
      const text = await r.text()
      const j = JSON.parse(text)
      if (text.length > 1024 || typeof j.preparing !== 'boolean' || typeof j.checking !== 'boolean') throw new Error(`본문 ${text.slice(0, 120)}`)
    })
  }, { prepOn: true, fakePrep: true })
}

for (const viewport of VIEWPORTS) {
  // ── 9. 성능 표시: 개발 표시일 때만 window.__ab.perf에 남고 목표 안이다 ──
  await flow('perf-dev', viewport, async (t) => {
    const { need, page } = t
    await need('튜터를 둘 다 시작해 둔다(방식 탭을 오가려면 대화가 있어야 한다)', async () => { await t.pick('chair'); await t.pick('guide') })
    await need('누름 → 첫 화면 변화가 200ms 이하로 남는다', async () => {
      await page.locator('#way-tabs [data-way="chair"]').click()
      await page.waitForFunction(() => window.__ab && window.__ab.perf && typeof window.__ab.perf.press_to_paint_ms === 'number', null, { timeout: 3000 })
      const p = await t.perf()
      if (!(p.press_to_paint_ms >= 0 && p.press_to_paint_ms <= 200)) throw new Error(`press_to_paint_ms=${p.press_to_paint_ms}`)
    })
    await need('방식 탭 → 내용 바뀜이 200ms 이하다', async () => {
      await page.locator('#way-tabs [data-way="guide"]').click()
      await page.waitForFunction(() => document.querySelector('#way-tabs [data-way="guide"]').getAttribute('aria-selected') === 'true')
      await sleep(300)
      const p = await t.perf()
      if (!(p.tab_to_change_ms >= 0 && p.tab_to_change_ms <= 200)) throw new Error(`tab_to_change_ms=${p.tab_to_change_ms}`)
    })
    await need('보내기 → 입력 칸 비움이 100ms 이하다', async () => {
      await page.locator('#say').fill('시간을 재는 말')
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 2000 })
      await sleep(300)
      const p = await t.perf()
      if (!(p.send_to_clear_ms >= 0 && p.send_to_clear_ms <= 100)) throw new Error(`send_to_clear_ms=${p.send_to_clear_ms}`)
    })
    await need('대화 60개 + 블록 8개의 전체 다시 그리기가 50ms 이하다', async () => {
      t.mutate = (json) => {
        const chat = json.session.guide || [], seed = chat[chat.length - 1]
        if (seed) while (chat.length < 60) chat.push({ ...seed, id: `m-${chat.length}`, text: `튜터 말 ${chat.length}` })
        const blocks = json.session.blocks || []
        const base = blocks[blocks.length - 1]
        if (base) while (blocks.length < 8) blocks.push({ ...base, id: `b-${blocks.length}` })
        return json
      }
      // 내용이 바뀌는 실제 다시 그리기를 잰다(같은 HTML 건너뛰기가 아니다). 상태를 받은 직후 읽어 뒤의 건너뛰기가 값을 덮지 않게 한다
      const p = await page.evaluate(async () => {
        const before = document.querySelectorAll('#chat-log .msg.tutor').length
        await loadState(true)
        return { before, after: document.querySelectorAll('#chat-log .msg.tutor').length, ms: window.__ab.perf.rerender_ms }
      })
      if (!(p.after >= 60 && p.after > p.before)) throw new Error(`내용이 바뀌지 않았다(${p.before} → ${p.after})`)
      if (!(p.ms >= 0 && p.ms <= 50)) throw new Error(`rerender_ms=${p.ms}`)
    })
    await need('300줄 코드에 100자를 쳐도 50ms 넘는 긴 작업이 2회 이하다', async () => {
      await t.direct()
      await page.locator('#code').fill(Array.from({ length: 300 }, (_, i) => `x${i} = ${i}`).join('\n'))
      await sleep(500)
      const before = await page.evaluate(() => window.__long)
      await page.locator('#code').click()
      await page.keyboard.type('a'.repeat(100), { delay: 5 })
      await sleep(500)
      const n = (await page.evaluate(() => window.__long)) - before
      if (n > 2) throw new Error(`긴 작업 ${n}회`)
    })
  }, { dev: true })
  await flow('perf-off', viewport, async (t) => {
    const { need, page } = t
    await need('개발 표시가 아니면 반응 시간을 남기지 않는다', async () => {
      await t.pick('chair')
      await page.locator('#way-tabs [data-way="solo"]').click()
      await sleep(300)
      if (await t.perf()) throw new Error('window.__ab.perf가 있다')
    })
  }, { dev: false })

  // ── 10. 방식 탭으로 튜터를 시작할 때 '다시 시작' 단추가 잠깐이라도 보이지 않는다(상태 응답을 늦춰도) ──
  await flow('no-start-again-flash', viewport, async (t) => {
    const { need, page } = t
    await need('튜터의 질문으로를 정상 시작한다', () => t.pick('chair'))
    await need('시작하는 동안 ‘다시 시작’이 한 번도 보이지 않았다', async () => {
      await sleep(1500)
      const seen = await page.evaluate(() => window.__sa)
      if (seen) throw new Error(`${seen}번 보였다`)
    })
  }, { stateDelay: 300 })

  // ── 11. 서버: 상태 응답이 빠르다 ──
  await flow('state-speed', viewport, async (t) => {
    const { need, page } = t
    await need('/api/state 중앙값이 250ms 이하다', async () => {
      const ms = []
      for (let i = 0; i < 7; i++) { const s = Date.now(); const r = await page.request.post(`${base}/api/state`, { data: { id: problem.id } }); if (!r.ok()) throw new Error(`상태 ${r.status()}`); ms.push(Date.now() - s) }
      ms.sort((a, b) => a - b)
      if (ms[3] > 250) throw new Error(`중앙값 ${ms[3]}ms`)
    })
  })
}
await browser.close()
process.exit(failed ? 1 : 0)
