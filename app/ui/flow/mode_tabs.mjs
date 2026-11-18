// 흐름 시험: 푸는 방식 탭. 세 방식이 늘 보이는 탭이고, 한 번 누르면 바뀌며, 대화는 방식마다 그대로이고, 다시 열어도 이어진다.
// 쓰는 법: node mode_tabs.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 연결 상태는 화면이 읽는 /api/accounts 응답으로만 바꾼다(키를 넣지 않는다). 튜터 시작은 저장된 계획의 첫 질문이라 모델 0회여야 한다(test_flow.py가 끝에서 센다).
// 고른 이름: 탭 묶음 #way-tabs(role=tablist), 탭 button[role=tab][data-way=solo|chair|guide], 대화 #chat-log, 제목 #way-title.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node mode_tabs.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const PID = 'hash_1_popular_shelf' // 미리 만든 풀이 순서(계획)가 실린 기본 문제
// 아직 열지 않은 기본 문제(계획과 검증된 풀이가 실려 있다). 걸음마다 하나씩 꺼내 쓴다(앞 걸음의 대화·방식이 남지 않게)
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const FRESH = builtin.filter((p) => p.id !== PID && p.ready && p.solutions && p.solutions.python)
const within = (promise, ms, what) => Promise.race([promise, new Promise((_, no) => setTimeout(() => no(new Error(`${what}: ${ms}ms 넘음`)), ms))])
const DRAFT_IDS = ['say', 'fq-text', 'debug-say', 'run-input'] // 문제마다 담아 두는 보내지 않은 글 칸
const chatShown = (p) => p.waitForFunction(() => { const el = document.getElementById('chat-log'); return el && !el.hidden && el.innerText.trim().length > 0 }, null, { timeout: 8000 })
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const TAB = (way) => `#way-tabs [role="tab"][data-way="${way}"]`
const browser = await launch()
let failed = 0

async function open(context, viewport, connected, problems, pid = PID) {
  const page = await context.newPage()
  await page.setViewportSize(viewport)
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
  await page.route('**/*', async (route) => {
    const url = route.request().url()
    if (url.startsWith(`${new URL(base).origin}/`)) {
      if (new URL(url).pathname === '/api/accounts') { // 키를 넣지 않고 연결 상태만 바꾼다
        const res = await route.fetch()
        return route.fulfill({ response: res, json: { ...(await res.json()), connected } })
      }
      return route.continue()
    }
    if (/^(data|blob|about):/.test(url)) return route.continue()
    problems.push(`external: ${url}`)
    return route.abort()
  })
  await page.goto(`${base}/#/p/${pid}`)
  return page
}

for (const viewport of VIEWPORTS) {
  const tag = `${viewport.width}x${viewport.height}`
  const problems = []
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  const context = await browser.newContext()
  const page = await open(context, viewport, true, problems)
  const selected = (way) => page.locator(TAB(way)).getAttribute('aria-selected')
  const chatText = () => page.locator('#chat-log').innerText()
  const pressTab = async (way) => {
    await page.locator(TAB(way)).click()
    await page.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB(way), { timeout: 2000 })
  }
  const tabReady = (p, way) => p.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB(way), { timeout: 5000 })
  const chatReady = () => page.waitForFunction(() => { const el = document.getElementById('chat-log'); return el && !el.hidden && el.innerText.trim().length > 0 }, null, { timeout: 5000 })

  // 1. 세 방식이 늘 보이는 탭 묶음. 처음 연 문제는 혼자 풀기. 옛 단추·카드·시작 단추가 없다
  await need('제목이 보인다', () => page.waitForFunction((t) => document.getElementById('p-title')?.textContent.trim().length > 0, null, { timeout: 5000 }))
  await need('탭 묶음에 세 방식이 보인다', async () => {
    await page.locator('#way-tabs[role="tablist"]').waitFor({ state: 'visible', timeout: 3000 })
    for (const way of ['solo', 'chair', 'guide']) await page.locator(TAB(way)).waitFor({ state: 'visible', timeout: 1000 })
    if ((await page.locator('#way-tabs [role="tab"][data-way]').count()) !== 3) throw new Error('탭이 셋이 아니다')
  })
  await need('처음 연 문제는 혼자 풀기가 골라져 있다', async () => {
    const got = await Promise.all(['solo', 'chair', 'guide'].map(selected))
    if (got.join() !== 'true,false,false') throw new Error(got.join())
  })
  await need('방식 바꾸기·그대로 두기·카드 화면·시작 단추가 없다', async () => {
    for (const sel of ['#way-change', '#start', '.way-card', '#way-box .wayrow']) if (await page.locator(sel).isVisible()) throw new Error(`보인다: ${sel}`)
    const body = await page.locator('body').innerText()
    for (const word of ['방식 바꾸기', '그대로 두기', '어떻게 풀까요?']) if (body.includes(word)) throw new Error(`글이 남아 있다: ${word}`)
  })
  const soloTitle = await page.locator('#way-title').innerText().catch(() => '')

  // 2. 튜터 탭: 한 번 누르면 바뀌고 대화가 없으면 스스로 첫 질문(저장된 계획이라 모델 0회)
  let chairText = '', guideText = ''
  await need('의자 탭 한 번에 바뀐다(aria-selected·제목)', async () => {
    await pressTab('chair')
    if ((await selected('solo')) !== 'false') throw new Error('혼자 풀기가 아직 골라져 있다')
    if ((await page.locator('#way-title').innerText()) === soloTitle) throw new Error('제목이 그대로다')
  })
  await need('의자: 누르기만 했는데 첫 질문이 나온다', async () => { await chatReady(); chairText = await chatText() })
  await need('가이드 탭도 한 번에 바뀌고 첫 질문이 나온다', async () => { await pressTab('guide'); await chatReady(); guideText = await chatText() })
  await need('혼자 풀기로 가면 대화 칸이 숨는다', async () => {
    await pressTab('solo')
    await page.waitForFunction(() => document.getElementById('chat-log')?.hidden !== false, null, { timeout: 2000 })
  })
  // 3. 혼자 → 의자 → 가이드 → 의자로 오가도 각 대화가 그대로
  await need('의자로 돌아오면 의자 대화가 그대로다', async () => {
    await pressTab('chair'); await chatReady()
    const now = await chatText()
    if (now !== chairText) throw new Error(`바뀌었다: ${JSON.stringify(now.slice(0, 60))}`)
  })
  await need('가이드로 돌아오면 가이드 대화가 그대로다', async () => {
    await pressTab('guide'); await chatReady()
    const now = await chatText()
    if (now !== guideText) throw new Error(`바뀌었다: ${JSON.stringify(now.slice(0, 60))}`)
  })
  await need('의자 대화는 다시 시작하지 않고 그대로다(같은 글이 두 번 쌓이지 않는다)', async () => {
    await pressTab('chair'); await chatReady()
    if ((await chatText()) !== chairText) throw new Error('의자 대화가 바뀌었다')
  })
  // 4. 방향키로 탭을 옮기면 초점과 함께 고른 방식도 바뀐다(→ 뒤에 가이드, ← 뒤에 의자를 따로 본다)
  const arrow = async (key, way, text) => {
    await page.keyboard.press(key)
    await page.waitForFunction((t) => document.activeElement === document.querySelector(t), TAB(way), { timeout: 1500 })
    if ((await selected(way)) !== 'true') throw new Error(`${key} 뒤 초점만 옮기고 ${way}가 골라지지 않았다`)
    await chatReady()
    if ((await chatText()) !== text) throw new Error(`${key} 뒤 ${way} 대화가 보이지 않는다`)
  }
  await need('→로 가이드를 고른다', async () => { await page.locator(TAB('chair')).focus(); await arrow('ArrowRight', 'guide', guideText) })
  await need('←로 의자를 고른다', () => arrow('ArrowLeft', 'chair', chairText))
  // 5. 고른 방식은 브라우저가 아닌 서버에 남는다: 저장소가 비어 있는 새 브라우저 문맥에서 같은 방식
  await need('방식을 localStorage에 두지 않는다', async () => {
    const keys = await page.evaluate(() => Object.keys(localStorage).filter((k) => /way/i.test(k)))
    if (keys.length) throw new Error(keys.join())
  })
  await pressTab('guide').catch(() => {})
  await need('새 문맥(저장소 없음)에서 열어도 같은 방식이다', async () => {
    const other = await open(await browser.newContext(), viewport, true, problems)
    try {
      await other.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB('guide'), { timeout: 5000 })
    } finally { await other.context().close() }
  })
  await need('새로 고쳐도 같은 방식과 같은 대화다', async () => {
    await page.reload()
    await page.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB('guide'), { timeout: 5000 })
    await chatReady()
    if ((await chatText()) !== guideText) throw new Error('대화가 달라졌다')
  })
  await need('가로 넘침이 없다', async () => { if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)) throw new Error('가로로 넘친다') })

  // 6. 보내지 않은 글과 결과 줄은 문제마다 남는다: 다른 문제를 열었다 돌아와도 그대로, 다른 문제에는 옮겨 가지 않는다
  const mine = FRESH.shift(), other = FRESH.shift()
  const drafts = await open(context, viewport, true, problems, mine.id)
  const draft = '아직 보내지 않은 생각'
  const go = (pid) => drafts.evaluate((h) => { location.hash = h }, `#/p/${pid}`)
  const titleOf = (pid) => drafts.waitForFunction((id) => location.hash.endsWith(id) && document.getElementById('p-title')?.textContent.trim().length > 0, pid, { timeout: 5000 })
  let verdict = ''
  await need('의자 대화에 보내지 않은 글을 쓰고 예시를 실행한다', async () => {
    await tabReady(drafts, 'solo')
    await drafts.locator('#code').fill(mine.solutions.python)
    await drafts.locator(TAB('chair')).click()
    await chatShown(drafts)
    await drafts.locator('#say').fill(draft)
    await drafts.locator('#run').click()
    await drafts.locator('#result .verdict').waitFor({ state: 'visible', timeout: 15000 })
    verdict = await drafts.locator('#result .verdict').innerText()
  })
  await need('다른 문제의 글 칸은 비어 있다', async () => {
    await go(other.id); await titleOf(other.id)
    if ((await drafts.locator('#say').inputValue()) !== '') throw new Error('다른 문제의 #say에 글이 옮겨 왔다')
    if (await drafts.locator('#result .verdict').count()) throw new Error('다른 문제에 결과 줄이 옮겨 왔다')
  })
  await need('돌아오면 글과 결과 줄이 다시 보인다', async () => {
    await go(mine.id); await titleOf(mine.id); await chatShown(drafts)
    await drafts.locator('#say').waitFor({ state: 'visible', timeout: 2000 })
    if ((await drafts.locator('#say').inputValue()) !== draft) throw new Error('보내지 않은 글이 사라졌다')
    await drafts.locator('#result .verdict').waitFor({ state: 'visible', timeout: 2000 })
    if ((await drafts.locator('#result .verdict').innerText()) !== verdict) throw new Error('결과 줄이 달라졌다')
  })

  // 7. 실행이 끝나기 전에 튜터 탭을 누르면 실행이 끝난 뒤 한 번만 시작한다(실행 요청을 붙잡아 둔다)
  const runner = FRESH.shift()
  const late = await open(context, viewport, true, problems, runner.id)
  let starts = 0, held, letRun
  const runHeld = new Promise((r) => { held = r })
  const runGate = new Promise((r) => { letRun = r })
  late.on('request', (r) => { if (r.url().endsWith('/api/turn') && r.postDataJSON()?.event === 'start') starts++ })
  await late.route('**/api/run', async (route) => { held(); await runGate; return route.fallback() })
  await need('실행 중 의자 탭을 누르면 시작하지 않고 기다린다', async () => {
    await tabReady(late, 'solo')
    await late.locator('#code').fill(runner.solutions.python)
    await late.locator('#run').click()
    await within(runHeld, 5000, '예시 실행 요청')
    await late.locator(TAB('chair')).click()
    await late.waitForTimeout(400)
    if (starts !== 0) throw new Error(`실행 중에 시작했다(${starts}회)`)
  })
  letRun()
  await need('실행이 끝나면 한 번 시작한다', async () => {
    await chatShown(late)
    await late.waitForTimeout(400)
    if (starts !== 1) throw new Error(`시작 요청 ${starts}회`)
  })

  // 8. 탭을 누를 때 보낸 상태 요청이 시작 뒤의 상태보다 늦게 와도 첫 질문을 덮지 않는다
  const racer = FRESH.shift()
  const race = await open(context, viewport, true, problems, racer.id)
  let armed = false, fetched, letOld, sent
  const oldFetched = new Promise((r) => { fetched = r })
  const oldGate = new Promise((r) => { letOld = r })
  const oldSent = new Promise((r) => { sent = r })
  await race.route('**/api/state', async (route) => {
    if (!armed) return route.fallback()
    armed = false // 탭을 누른 뒤 첫 상태 요청: 시작 전의 상태를 받아 두고, 시작 뒤의 상태가 그려진 다음에 건넨다
    const res = await route.fetch()
    fetched()
    await oldGate
    await route.fulfill({ response: res })
    sent()
  })
  await race.route('**/api/turn', async (route) => { await within(oldFetched, 5000, '앞 상태 요청').catch(() => {}); return route.fallback() }) // 시작은 앞 상태를 받은 뒤에
  let first = ''
  await need('의자 탭을 누르면 첫 질문이 나온다(앞 상태 응답은 붙잡아 둔다)', async () => {
    await tabReady(race, 'solo')
    armed = true
    await race.locator(TAB('chair')).click()
    await chatShown(race)
    first = await race.locator('#chat-log').innerText()
  })
  letOld()
  await need('늦게 온 앞 상태 응답이 첫 질문을 지우지 않는다', async () => {
    await within(oldSent, 3000, '붙잡은 상태 응답')
    await race.waitForTimeout(400)
    if (!(await race.locator('#chat-log').isVisible()) || (await race.locator('#chat-log').innerText()) !== first) throw new Error('늦은 상태 응답이 대화를 옛 상태로 덮었다')
  })

  // 9. 더 정확한 풀이로 바꿔 끼우면(대화가 지워진다) 튜터가 한 번 더 시작한다. 시작한 뒤 대화만 지워지면 '다시 시작' 단추가 남는다
  const swapper = FRESH.shift()
  const swap = await open(context, viewport, true, problems, swapper.id)
  let swapStarts = 0, better = true
  swap.on('request', (r) => { if (r.url().endsWith('/api/turn') && r.postDataJSON()?.event === 'start') swapStarts++ })
  const wipe = () => swap.request.post(`${base}/api/reset`, { data: { id: swapper.id } }) // 서버의 대화를 지운다(계획은 남는다)
  await swap.route('**/api/state', async (route) => { // 바꿔 끼울 풀이가 있는 등록 문제처럼 보이게 한다(기본 문제에는 그 단추가 없다)
    const res = await route.fetch(), body = await res.json()
    return route.fulfill({ response: res, json: { ...body, problem: { ...body.problem, sample: false, better } } })
  })
  await swap.route('**/api/swap', async (route) => { await wipe(); better = false; return route.fulfill({ json: { ok: true } }) })
  await need('의자를 시작한 뒤 바꿔 끼우면 한 번 더 시작한다', async () => {
    await tabReady(swap, 'solo')
    await swap.locator(TAB('chair')).click()
    await chatShown(swap)
    if (swapStarts !== 1) throw new Error(`처음 시작 요청 ${swapStarts}회`)
    const again = swap.waitForResponse((r) => r.url().endsWith('/api/turn'), { timeout: 5000 })
    await swap.locator('#swap-guide').click()
    await again
    await chatShown(swap)
    if (swapStarts !== 2) throw new Error(`시작 요청 ${swapStarts}회`)
  })
  await need('시작한 뒤 대화가 지워지면 스스로 다시 시작하지 않고 다시 시작 단추를 둔다', async () => {
    await wipe()
    await swap.evaluate(() => loadState())
    await swap.locator('#start-again').waitFor({ state: 'visible', timeout: 3000 })
    if (swapStarts !== 2) throw new Error(`스스로 다시 시작했다(${swapStarts}회)`)
    await swap.locator('#start-again').click()
    await chatShown(swap)
    if (swapStarts !== 3) throw new Error(`다시 시작 단추가 시작하지 않았다(${swapStarts}회)`)
  })

  // 10. 문제를 고쳐 저장하고 돌아오면, 고치기 전에 담아 둔 보내지 않은 글과 결과 줄을 되살리지 않는다
  let ed = null, ownId = null
  const edGo = (h) => ed.evaluate((x) => { location.hash = x }, h)
  const edAt = (pid, title) => ed.waitForFunction(([id, t]) => location.hash === `#/p/${id}` && (t ? document.getElementById('p-title')?.textContent.trim() === t : document.getElementById('p-title')?.textContent.trim().length > 0), [pid, title], { timeout: 5000 })
  await need('등록한 문제에서 넣을 값을 적어 두고 예시를 실행한다', async () => {
    const res = await page.request.post(`${base}/api/problems/new`, { data: { title: '두 수의 합', text: `두 정수 a, b의 합을 return 하도록 solution 함수를 완성하세요. (${tag})`, language: 'python', mode: 'function',
      cases: [{ input: '[1, 2]', expected: '3' }, { input: '[5, 5]', expected: '10' }] } })
    if (!res.ok()) throw new Error(`등록 ${res.status()}`)
    ownId = (await res.json()).id
    ed = await open(context, viewport, true, problems, ownId)
    await tabReady(ed, 'solo')
    await ed.locator('#code').fill('def solution(a, b):\n    return a + b\n')
    await ed.locator('#run-own summary').click()
    await ed.locator('#run-input').fill('[7, 8]')
    await ed.locator('#run').click()
    await ed.locator('#result .verdict').waitFor({ state: 'visible', timeout: 15000 })
  })
  await need('다른 문제를 열었다 돌아오면 그 글과 결과 줄이 남아 있다', async () => {
    await edGo(`#/p/${other.id}`); await edAt(other.id)
    await edGo(`#/p/${ownId}`); await edAt(ownId)
    if ((await ed.locator('#run-input').inputValue()) !== '[7, 8]') throw new Error('넣을 값이 사라졌다')
    await ed.locator('#result .verdict').waitFor({ state: 'visible', timeout: 2000 })
  })
  await need('고쳐 저장한 뒤에는 글 칸이 비고 결과 줄이 없다', async () => {
    await edGo(`#/edit/${ownId}`)
    await ed.waitForFunction(() => document.getElementById('new-title')?.value.trim().length > 0, null, { timeout: 5000 })
    await ed.locator('#new-title').fill('두 수의 합 고침')
    await ed.locator('#new-next').click()
    await ed.locator('#new-submit').click()
    await edAt(ownId, '두 수의 합 고침')
    for (const id of DRAFT_IDS) if ((await ed.locator(`#${id}`).inputValue()) !== '') throw new Error(`#${id}에 고치기 전 글이 돌아왔다`)
    if (await ed.locator('#result .verdict').count()) throw new Error('고치기 전 케이스로 받은 결과 줄이 돌아왔다')
  })

  // 11. 연결이 없으면 튜터 탭 안에 연결 안내 카드(탭은 그대로 보이고, 모델은 부르지 않는다). 그 탭은 방식으로 남지 않는다
  const off = await open(await browser.newContext(), viewport, false, problems)
  const kept = [] // 연결이 없을 때 보낸 방식 저장 요청
  off.on('request', (r) => { if (r.url().endsWith('/api/way')) kept.push(r.postDataJSON()?.way) })
  await need('연결이 없어도 세 탭이 보인다', async () => { for (const way of ['solo', 'chair', 'guide']) await off.locator(TAB(way)).waitFor({ state: 'visible', timeout: 4000 }) })
  await need('연결이 없을 때 튜터 탭 안에 연결 안내 카드가 있다', async () => {
    await off.locator(TAB('chair')).click()
    await off.locator('#pane-tutor a[href^="#/settings"]').first().waitFor({ state: 'visible', timeout: 3000 })
    if (await off.locator('#chat-log').isVisible()) throw new Error('연결이 없는데 대화 칸이 보인다')
  })
  await need('연결 카드에서 혼자 풀기 탭으로 돌아올 수 있다', async () => {
    const saved = off.waitForResponse((r) => r.url().endsWith('/api/way') && r.request().postDataJSON()?.way === 'solo', { timeout: 3000 })
    await off.locator(TAB('solo')).click()
    await off.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB('solo'), { timeout: 2000 })
    await saved
  })
  await need('연결이 없을 때 누른 튜터 탭은 방식으로 남지 않는다', async () => { if (kept.some((w) => w !== 'solo')) throw new Error(`남긴 방식: ${kept.join()}`) })

  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `mode_tabs-${tag}.png`) }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await context.close()
  await off.context().close()
}
await browser.close()
process.exit(failed ? 1 : 0)
