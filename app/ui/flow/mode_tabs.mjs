// 흐름 시험: 푸는 방식 탭. 세 방식이 늘 보이는 탭이고, 한 번 누르면 바뀌며, 대화는 방식마다 그대로이고, 다시 열어도 이어진다.
// 쓰는 법: node mode_tabs.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 연결 상태는 화면이 읽는 /api/accounts 응답으로만 바꾼다(키를 넣지 않는다). 튜터 시작은 저장된 계획의 첫 질문이라 모델 0회여야 한다(test_flow.py가 끝에서 센다).
// 고른 이름: 탭 묶음 #way-tabs(role=tablist), 탭 button[role=tab][data-way=solo|chair|guide], 대화 #chat-log, 제목 #way-title.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node mode_tabs.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const PID = 'hash_1_popular_shelf' // 미리 만든 풀이 순서(계획)가 실린 기본 문제
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const TAB = (way) => `#way-tabs [role="tab"][data-way="${way}"]`
const browser = await launch()
let failed = 0

async function open(context, viewport, connected, problems) {
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
  await page.goto(`${base}/#/p/${PID}`)
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
  // 4. 방향키로 탭을 옮긴다
  await need('방향키로 탭을 옮긴다', async () => {
    await page.locator(TAB('chair')).focus()
    await page.keyboard.press('ArrowRight')
    await page.waitForFunction((t) => document.activeElement === document.querySelector(t), TAB('guide'), { timeout: 1500 })
    await page.keyboard.press('ArrowLeft')
    await page.waitForFunction((t) => document.activeElement === document.querySelector(t), TAB('chair'), { timeout: 1500 })
    if ((await selected('chair')) !== 'true') throw new Error('초점은 옮겨도 고른 방식이 따라오지 않는다')
  })
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

  // 6. 연결이 없으면 튜터 탭 안에 연결 안내 카드(탭은 그대로 보이고, 모델은 부르지 않는다)
  const off = await open(await browser.newContext(), viewport, false, problems)
  await need('연결이 없어도 세 탭이 보인다', async () => { for (const way of ['solo', 'chair', 'guide']) await off.locator(TAB(way)).waitFor({ state: 'visible', timeout: 4000 }) })
  await need('연결이 없을 때 튜터 탭 안에 연결 안내 카드가 있다', async () => {
    await off.locator(TAB('chair')).click()
    await off.locator('#pane-tutor a[href^="#/settings"]').first().waitFor({ state: 'visible', timeout: 3000 })
    if (await off.locator('#chat-log').isVisible()) throw new Error('연결이 없는데 대화 칸이 보인다')
  })
  await need('연결 카드에서 혼자 풀기 탭으로 돌아올 수 있다', async () => {
    await off.locator(TAB('solo')).click()
    await off.waitForFunction((t) => document.querySelector(t)?.getAttribute('aria-selected') === 'true', TAB('solo'), { timeout: 2000 })
  })

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
