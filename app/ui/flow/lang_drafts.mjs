// 흐름 시험: 언어를 바꿔도 튜터에게 아직 보내지 않은 글(대화 칸 #say, 디버그 칸 #debug-say)이 언어마다 남는다.
// 쓰는 법: node lang_drafts.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 연결 상태는 /api/accounts 응답으로만 바꾼다(키를 넣지 않는다). 보내기(/api/turn)·디버그 첫 질문(/api/debug)은 route가 꾸민 응답으로 받아 모델을 부르지 않는다.
// 기대: 언어마다 따로 남고, 돌아오면 되살고, 보내면 그 언어의 것만 비고, 문제를 옮겨도(바꾸기를 기다리는 동안 옮겨도) 섞이지 않고, 바꾸기가 실패해도 잃지 않고, 서버로 가는 요청에 글이 실리지 않는다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node lang_drafts.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const ready = builtin.filter((p) => p.language === 'python' && p.ready && p.ready.plan && p.ready.plan.blocks.length > 1)
const problem = ready.filter((p) => p.readies && Object.keys(p.readies).length && p.solutions && p.solutions.python).at(-1)
const second = ready.find((p) => p.id !== problem.id)
const other = Object.keys(problem.readies)[0]
const WRONG = `${problem.solutions.python.split('\n').find((l) => l.startsWith('def solution'))}\n    return None\n` // 어떤 기본 문제에서도 틀리는 코드(함수 머리만 두고 아무것도 돌려주지 않는다)
const A = '파이썬에서 쓰던 답 ㄱ-초안', B = `${other}에서 쓰던 답 ㄴ-초안`, DA = '파이썬 디버그 ㄷ-초안', DB = `${other} 디버그 ㄹ-초안`, Q = '다른 문제에서 쓰던 답 ㅁ-초안', R = '파이썬 실행 입력 ㅂ-초안'
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

/** 한 걸음(흐름 × 뷰포트)을 새 문맥·새 화면에서 돌린다. 앞 걸음이 실패하면 뒤 걸음은 기다리지 않는다. */
async function flow(name, viewport, steps) {
  const tag = `${name}-${viewport.width}x${viewport.height}`
  const problems = [], sent = []
  let stuck = false, failLang = false, hold = null
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  const context = await browser.newContext({ viewport })
  context.setDefaultTimeout(5000)
  const page = await context.newPage()
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problems.push(`console: ${m.text()}`) })
  await page.route('**/*', async (route) => {
    const req = route.request(), url = new URL(req.url())
    if (url.origin !== new URL(base).origin) {
      if (/^(data|blob|about):/.test(req.url())) return route.continue()
      problems.push(`external: ${req.url()}`)
      return route.abort()
    }
    if (url.pathname === '/api/accounts') {
      const res = await route.fetch()
      return route.fulfill({ response: res, json: { ...(await res.json()), connected: true } })
    }
    if (req.method() === 'POST' && url.pathname.startsWith('/api/')) sent.push({ path: url.pathname, body: req.postData() || '' })
    let body = {}
    try { body = JSON.parse(req.postData() || '{}') } catch {}
    if (url.pathname === '/api/language' && hold) { const h = hold; hold = null; const res = await route.fetch(); h.got(); await h.wait; return route.fulfill({ response: res }) }
    if (url.pathname === '/api/language' && failLang) { failLang = false; return route.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ detail: { code: 'llm_timeout', message: '모델이 답하지 않았어요' } }) }) }
    if (url.pathname === '/api/turn' && body.event === 'message') return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    if (url.pathname === '/api/debug') return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: '어디서 값이 사라질까요?', passed: false, line: null }) })
    return route.continue()
  })
  const post = async (path, data) => { const r = await context.request.post(`${base}${path}`, { data }); if (!r.ok()) problems.push(`${path} ${r.status()}`) }
  for (const p of [problem, second]) { await post('/api/language', { id: p.id, language: 'python' }); await post('/api/reset', { id: p.id }) }
  await page.goto(`${base}/#/p/${problem.id}`)
  const t = {
    page, need,
    failNextLang: () => { failLang = true },
    holdNextLang: () => { // 다음 바꾸기 응답을 release()까지 붙잡는다(서버는 이미 바꿨다). reached: 붙잡았을 때
      let release, got
      const wait = new Promise((r) => { release = r }), reached = new Promise((r) => { got = r })
      hold = { wait, got }
      return { reached, release }
    },
    title: (p) => page.waitForFunction((s) => (document.getElementById('p-title')?.textContent || '').includes(s), p.title, { timeout: 10000 }),
    value: (id) => page.locator(`#${id}`).inputValue(),
    expect: async (id, want, what) => { const got = await page.locator(`#${id}`).inputValue(); if (got !== want) throw new Error(`${what}: #${id}가 ${JSON.stringify(got)}(기대 ${JSON.stringify(want)})`) },
    settled: (language) => page.waitForFunction((l) => document.getElementById('p-lang-select')?.value === l && !document.getElementById('p-lang-select').disabled
      && !document.querySelector('#chat-log .msg.tutor.pending') && document.querySelectorAll('#chat-log .msg.tutor:not(.pending)').length > 0, language, { timeout: 10000 }),
    choose: async (language) => {
      const done = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/language', { timeout: 5000 })
      await page.locator('#p-lang-select').selectOption(language)
      await done
      await t.settled(language)
    },
    start: async (way = 'guide') => {
      await t.title(problem)
      await page.locator(`#way-tabs [data-way="${way}"]`).click()
      await page.locator('#chat-log .msg.tutor:not(.pending)').first().waitFor({ state: 'visible', timeout: 10000 })
    },
    sent,
  }
  try { await steps(t) } catch (e) { problems.push(`steps: ${String(e.message).split('\n')[0]}`) }
  const leaked = sent.filter((q) => q.path !== '/api/turn' && q.path !== '/api/debug' && [A, B, DA, DB, Q, R].some((s) => q.body.includes(s)))
  if (leaked.length) problems.push(`서버로 가는 요청에 입력 칸 글이 실렸다: ${leaked.map((q) => q.path).join(', ')}`)
  await post('/api/language', { id: problem.id, language: 'python' })
  await post('/api/reset', { id: problem.id })
  await post('/api/reset', { id: second.id })
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `lang_drafts-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.unrouteAll({ behavior: 'ignoreErrors' })
  await context.close()
}

for (const viewport of VIEWPORTS) {
  // ── 1. 대화 칸: 언어마다 따로 남고 돌아오면 되살아난다 ──
  await flow('chat-round-trip', viewport, async (t) => {
    const { need, page } = t
    await need('튜터와 차례로를 시작한다', () => t.start())
    await need('파이썬에서 보내지 않은 글을 적는다', () => page.locator('#say').fill(A))
    await need(`${other}로 바꾸면 처음 보는 언어라 대화 칸이 비어 있다`, async () => { await t.choose(other); await t.expect('say', '', `${other} 처음`) })
    await need(`${other}에서 다른 글을 적는다`, () => page.locator('#say').fill(B))
    await need('파이썬으로 돌아오면 파이썬의 글이다', async () => { await t.choose('python'); await t.expect('say', A, '파이썬 복귀') })
    await need(`${other}로 다시 가면 ${other}의 글이다`, async () => { await t.choose(other); await t.expect('say', B, `${other} 복귀`) })
  })

  // ── 2. 디버그 칸: 같다 ──
  await flow('debug-round-trip', viewport, async (t) => {
    const { need, page } = t
    await need('튜터와 차례로를 시작한다', () => t.start('chair'))
    await need('틀린 코드를 돌려 ‘틀린 곳 같이 찾기’를 연다', async () => {
      await page.evaluate(() => { setCodeTab('direct', 'quiet'); render() })
      await page.locator('#code').fill(WRONG)
      await page.locator('#run').click()
      await page.waitForFunction(() => document.querySelector('#result .verdict'), null, { timeout: 15000 })
      await page.locator('#debug-start').click()
      await page.locator('#debug-say').waitFor({ state: 'visible', timeout: 5000 })
    })
    await need('파이썬 디버그 칸에 적는다', () => page.locator('#debug-say').fill(DA))
    await need(`${other}로 바꾸면 디버그 칸이 비어 있다`, async () => { await t.choose(other); await t.expect('debug-say', '', `${other} 처음`) })
    await need(`${other} 디버그 칸에 적는다(열려 있지 않아도 칸의 값으로 본다)`, () => page.evaluate((v) => { const el = document.getElementById('debug-say'); el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })) }, DB))
    await need('파이썬으로 돌아오면 파이썬 디버그 글이다', async () => { await t.choose('python'); await t.expect('debug-say', DA, '파이썬 복귀') })
    await need(`${other}로 다시 가면 ${other} 디버그 글이다`, async () => { await t.choose(other); await t.expect('debug-say', DB, `${other} 복귀`) })
  })

  // ── 3. 보낸 뒤에는 그 언어의 기억만 비워진다 ──
  await flow('send-clears-that-language', viewport, async (t) => {
    const { need, page } = t
    await need('튜터와 차례로를 시작한다', () => t.start())
    await need('파이썬에서 적고, 다른 언어에서도 적는다', async () => {
      await page.locator('#say').fill(A)
      await t.choose(other)
      await page.locator('#say').fill(B)
      await t.choose('python')
      await t.expect('say', A, '파이썬 복귀')
    })
    await need('파이썬에서 보내면 칸이 빈다', async () => {
      await page.locator('#send').click()
      await page.waitForFunction(() => document.getElementById('say').value === '', null, { timeout: 5000 })
    })
    await need(`${other}로 가면 ${other}의 글은 그대로다`, async () => { await t.choose(other); await t.expect('say', B, `${other} 남음`) })
    await need('파이썬으로 돌아오면 보낸 글이 되살아나지 않는다', async () => { await t.choose('python'); await t.expect('say', '', '보낸 글') })
  })

  // ── 4. 문제를 옮겨도 섞이지 않는다(문제마다·언어마다 따로) ──
  await flow('problem-switch', viewport, async (t) => {
    const { need, page } = t
    await need('튜터와 차례로를 시작한다', () => t.start())
    await need(`이 문제의 파이썬·${other} 글을 적는다`, async () => {
      await page.locator('#say').fill(A)
      await t.choose(other)
      await page.locator('#say').fill(B)
    })
    await need('다른 문제를 열면 그 문제의 칸은 이 문제의 글이 아니다', async () => {
      await page.evaluate((id) => { location.hash = `#/p/${id}` }, second.id)
      await t.title(second)
      const v = await t.value('say')
      if (v === A || v === B) throw new Error(`다른 문제의 칸에 ${JSON.stringify(v)}가 넘어왔다`)
    })
    await need('다른 문제에서 적은 글이 있다', async () => { await page.locator('#way-tabs [data-way="guide"]').click(); await page.locator('#say').fill(Q) })
    await need(`처음 문제로 돌아오면 ${other}의 글이 그대로다(문제를 옮기면 비움 쪽이면 빈 칸)`, async () => {
      await page.evaluate((id) => { location.hash = `#/p/${id}` }, problem.id)
      await t.title(problem)
      await t.settled(other)
      const v = await t.value('say')
      if (v === Q || v === A) throw new Error(`섞였다: ${JSON.stringify(v)}`)
      if (v !== B && v !== '') throw new Error(`엉뚱한 글: ${JSON.stringify(v)}`)
      if (v === '') throw new Error('문제를 옮기기 전의 글이 사라졌다(지금 동작은 문제마다 남긴다)')
    })
    await need('파이썬으로 바꾸면 파이썬의 글이다', async () => { await t.choose('python'); await t.expect('say', A, '파이썬 복귀') })
  })

  // ── 5. 바꾸기가 실패하면 글을 잃지 않는다 ──
  await flow('failed-switch', viewport, async (t) => {
    const { need, page } = t
    await need('튜터와 차례로를 시작한다', () => t.start())
    await need('적고 바꾸기가 실패하게 한다', async () => {
      await page.locator('#say').fill(A)
      t.failNextLang()
      const done = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/language', { timeout: 5000 })
      await page.locator('#p-lang-select').selectOption(other)
      await done
      await page.waitForFunction(() => !document.getElementById('p-lang-select').disabled && !document.querySelector('#chat-log .msg.tutor.pending'), null, { timeout: 10000 })
    })
    await need('실패한 뒤에도 입력 칸 글이 남아 있다', () => t.expect('say', A, '실패 뒤'))
    await need('다시 바꾸면 되고, 돌아오면 글이 남아 있다', async () => {
      await page.locator('#say').fill(A)
      await t.choose(other)
      await t.expect('say', '', `${other} 처음`)
      await t.choose('python')
      await t.expect('say', A, '파이썬 복귀')
    })
  })

  // ── 6. 바꾸기 응답을 기다리는 동안 다른 문제로 옮겼다 돌아와도 언어마다 따로 남는다 ──
  await flow('switch-away-while-changing', viewport, async (t) => {
    const { need, page } = t
    let held = null
    await need('튜터와 차례로를 시작한다', () => t.start())
    await need('파이썬에서 틀린 코드를 실행해 결과를 만들고 실행 입력 칸에 적는다', async () => {
      await page.evaluate(() => { setCodeTab('direct', 'quiet'); render() })
      await page.locator('#code').fill(WRONG)
      await page.locator('#run').click()
      await page.locator('#result .verdict').waitFor({ state: 'visible', timeout: 15000 })
      await page.locator('#run-own summary').click()
      await page.locator('#run-input').fill(R)
    })
    await need(`파이썬 글을 적고 ${other}로 바꾸는 응답을 붙잡아 둔다`, async () => {
      await page.locator('#say').fill(A)
      held = t.holdNextLang()
      await page.locator('#p-lang-select').selectOption(other)
      await held.reached
    })
    await need('응답이 오기 전에 다른 문제로 옮긴다', async () => {
      await page.evaluate((id) => { location.hash = `#/p/${id}` }, second.id)
      await t.title(second)
    })
    await need('붙잡은 응답을 풀고 바꾸기가 끝날 때까지 기다린다', async () => {
      const done = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/language', { timeout: 5000 })
      held.release()
      await done
      await page.waitForFunction(() => !document.getElementById('p-lang-select').disabled, null, { timeout: 5000 })
    })
    await need(`처음 문제로 돌아오면 ${other} 칸은 비어 있다`, async () => {
      await page.evaluate((id) => { location.hash = `#/p/${id}` }, problem.id)
      await t.title(problem)
      await t.settled(other)
      await t.expect('say', '', `${other} 처음`)
    })
    await need('실행 입력 칸이 비어 있고 파이썬의 결과가 보이지 않는다(그 자리에서 바꿀 때처럼)', async () => {
      await t.expect('run-input', '', `${other} 처음`)
      if (await page.locator('#result .verdict').count()) throw new Error('앞 언어의 결과 줄이 남았다')
    })
    await need('파이썬으로 바꾸면 파이썬의 글이다', async () => { await t.choose('python'); await t.expect('say', A, '파이썬 복귀') })
  })
}
await browser.close()
process.exit(failed ? 1 : 0)
