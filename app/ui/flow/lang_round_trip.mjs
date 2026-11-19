// 흐름 시험: 언어를 바꿨다 돌아와도 튜터 대화(내가 보낸 블록 코드와 그 뒤의 말까지)와 블록 칸이 남는다. 바꿀 때 확인을 묻지 않는다.
// 쓰는 법: node lang_round_trip.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 연결 상태는 화면이 읽는 /api/accounts 응답으로만 바꾼다(키를 넣지 않는다). 두 언어 모두 실린 계획으로 시작해 모델 0회여야 한다(test_flow.py가 끝에서 센다).
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node lang_round_trip.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

// 파이썬 계획과 다른 언어의 계획이 함께 실린 기본 문제. 다른 흐름과 겹치지 않게 목록의 끝에서 고른다
const builtin = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'builtin.json'), 'utf8'))
const problem = builtin.filter((p) => p.ready && p.ready.plan && p.ready.plan.blocks.length > 1 && p.readies && Object.keys(p.readies).length).at(-1)
const other = Object.keys(problem.readies)[0]
const TYPED = 'x = 1  # 저장하기 전에 언어를 바꾼다'
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const browser = await launch()
let failed = 0

for (const viewport of VIEWPORTS) {
  const tag = `${viewport.width}x${viewport.height}`
  const problems = []
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  const context = await browser.newContext({ viewport })
  const page = await context.newPage()
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`) })
  await page.route('**/*', async (route) => {
    const url = route.request().url()
    if (url.startsWith(`${new URL(base).origin}/`)) {
      if (new URL(url).pathname === '/api/accounts') { // 키를 넣지 않고 연결 상태만 바꾼다
        const res = await route.fetch()
        return route.fulfill({ response: res, json: { ...(await res.json()), connected: true } })
      }
      return route.continue()
    }
    if (/^(data|blob|about):/.test(url)) return route.continue()
    problems.push(`external: ${url}`)
    return route.abort()
  })
  const post = async (path, data) => { const r = await context.request.post(`${base}${path}`, { data }); if (!r.ok()) problems.push(`${path} ${r.status()}`) }
  await post('/api/language', { id: problem.id, language: 'python' })
  await post('/api/reset', { id: problem.id }) // 앞 뷰포트의 대화·방식을 지운다(계획은 남는다)
  await page.goto(`${base}/#/p/${problem.id}`)

  const tutorSaid = () => page.locator('#chat-log .msg.tutor:not(.pending)').count()
  const chatTexts = () => page.locator('#chat-log .msg:not(.pending)').allInnerTexts() // 내 말과 튜터의 말
  const cell = () => page.locator('#blocks > li.block[aria-current="step"] textarea.codey')
  const choose = async (language) => { // 고르자마자 바꾸기 요청이 가고, 끝나면 그 언어의 대화가 보인다
    const sent = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/language', { timeout: 15000 }) // 느린 러너에서는 바꾸기 응답이 5초를 넘기도 한다
    await page.locator('#p-lang-select').selectOption(language)
    await sent
    await page.waitForFunction((l) => document.getElementById('p-lang-select')?.value === l && !document.getElementById('p-lang-select').disabled
      && document.querySelectorAll('#chat-log .msg.tutor:not(.pending)').length > 0, language, { timeout: 10000 })
  }
  let before = []

  await need('튜터와 차례로를 시작한다', async () => {
    await page.locator('#way-tabs [data-way="guide"]').click()
    await page.locator('#chat-log .msg.tutor:not(.pending)').first().waitFor({ state: 'visible', timeout: 10000 })
  })
  await need('첫 블록 코드를 보내 다음 블록의 말을 받는다(스스로 다시 시작해서는 나오지 않는 대화)', async () => {
    const said = await tutorSaid()
    await cell().fill(problem.ready.plan.blocks[0].reference)
    await page.locator('#blocks > li.block[aria-current="step"] [data-check]').click()
    await page.waitForFunction((n) => !document.querySelector('#chat-log .msg.tutor.pending') && document.querySelectorAll('#chat-log .msg.tutor:not(.pending)').length > n, said, { timeout: 15000 })
    before = await chatTexts()
    if (before.length < 3) throw new Error(`대화가 ${before.length}개뿐이다`)
  })
  await need(`블록 칸에 적자마자(저장 전) ${other}로 바꾼다`, async () => {
    await cell().fill(TYPED)
    await choose(other)
  })
  await need('바꿀 때 확인을 묻지 않는다', async () => { if (await page.locator('#lang-confirm, #lang-yes').count()) throw new Error('확인 묻기가 남았다') })
  await need(`${other}의 블록 칸은 비어 있다`, async () => { if ((await cell().inputValue()).trim()) throw new Error('파이썬 칸의 글이 넘어왔다') })
  await need('파이썬으로 돌아온다', async () => {
    await choose('python')
  })
  await need('파이썬에서 나눈 대화가 내가 보낸 말까지 그대로다', async () => {
    const now = await chatTexts()
    if (now.join('\n') !== before.join('\n')) throw new Error(`${before.length}개 → ${now.length}개`)
  })
  await need('저장 전에 바꾼 블록 칸의 글이 남아 있다', async () => { if ((await cell().inputValue()) !== TYPED) throw new Error(await cell().inputValue()) })
  await post('/api/language', { id: problem.id, language: 'python' }) // 중간에 실패해도 다른 언어로 남지 않게
  await post('/api/reset', { id: problem.id }) // 다음 흐름에 대화를 남기지 않는다
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `lang_round_trip-${tag}.png`), fullPage: false }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await context.close()
}
await browser.close()
process.exit(failed ? 1 : 0)
