// 흐름 시험: 튜터 말마다 블록 번호 표('블록 N/전체 · 종류')가 보이고, 꼬리질문 단추와 입력 칸은 없다.
// 쓰는 법: node block_badge.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델은 쓰지 않는다. 문제 상태 응답(/api/state)의 대화·블록을 route가 꾸며 주고, 연결은 된 것으로 답한다.
// 정한 이름(구현이 지킬 것):
//   표: 튜터 말 `.msg.tutor[data-msg]` 안의 `button.block-badge`(블록 번호가 있는 말마다 하나). 글 '블록 N/전체 · 종류', 이름은 없다.
//   읽는 글: 튜터 말 요소의 aria-label '블록 N에 대한 튜터 말', 표의 접근 가능한 이름(aria-label이 있으면 그것, 없으면 글)은 '블록 N'으로 시작한다.
//   누르면: 그 블록 칸(`#blocks > li`의 N번째)이 보이고 코드 칸에 초점이 간다(칸이 있을 때).
//   block_index가 없는 옛 말에는 표가 없다. 블록이 바뀔 때만 뜨던 구분선(.turn)은 없다. 옛 꼬리질문 기록은 읽기 전용으로 보인다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node block_badge.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const PID = 'hash_1_popular_shelf'
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const KINDS = ['var_from_problem', 'loop', 'condition', 'branch']
const LABEL = { var_from_problem: '문제에서 바로 오는 변수', loop: '반복', condition: '조건', branch: '분기' }
const OLD_ASK = '옛꼬리질문 for가 뭐예요?', OLD_ANSWER = '옛꼬리답 for는 되풀이하는 문법이에요.'
const at = '2026-10-15T00:00:00+09:00'
const svc = (id, text, block_index, move = 'clue') => ({ id, role: 'service', text, at, block_index, move })
const usr = (id, text, block_index) => ({ id, role: 'user', text, at, block_index, move: null })
// 블록 1에서 둘, 블록 2에서 하나, 블록 3(찾는 중)에서 하나, block_index가 없는 옛 말 하나
const CHAT = [
  svc('m1', '첫 질문이에요. 무엇부터 볼까요?', 0, 'open'), usr('m2', '입력을 봐요', 0), svc('m3', '그 값을 어디에 둘까요?', 0),
  svc('m4', '다음 질문이에요. 어떻게 되풀이할까요?', 1, 'open'), svc('m5', '이 자리에서 무엇을 가를까요?', 2, 'open'),
  { id: 'm6', role: 'service', text: '옛 기록의 말이에요.', at, block_index: null, move: null },
]
const WITH_INDEX = ['m1', 'm3', 'm4', 'm5'], EXPECT_NO = { m1: 1, m3: 1, m4: 2, m5: 3 }

const browser = await launch()
let failed = 0

async function flow(way, viewport) {
  const tag = `block_badge-${way}-${viewport.width}x${viewport.height}`
  const context = await browser.newContext({ viewport })
  context.setDefaultTimeout(4000)
  const page = await context.newPage()
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problems.push(`console: ${m.text()}`) })
  let total = 0
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
      if (s && s.blocks && s.blocks.length >= 4) {
        total = s.blocks.length
        s.blocks = s.blocks.map((b, i) => ({ ...b, kind: KINDS[i % 4], name: i < 2 || way === 'guide' ? `시험블록${i + 1}` : null })) // 의자에서 3번째 블록은 아직 못 찾았다
        s.open_count = 3
        s.chair = s.guide = CHAT
        s.followups = [{ quote_id: 'm4', messages: [usr('f1', OLD_ASK, null), { ...svc('f2', OLD_ANSWER, null, 'followup') }] }]
        return route.fulfill({ response: res, json })
      }
      return route.fulfill({ response: res, json })
    }
    if (url.pathname.startsWith('/api/') && url.pathname !== '/api/reset') {
      // 이 흐름은 모델을 부르지 않는다: 대화·블록을 바꾸는 요청이 나가면 실패로 센다
      if (/^\/api\/(turn|followup|fill|explain|feedback|debug)$/.test(url.pathname)) { problems.push(`모델 요청: ${url.pathname}`); return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }) }
    }
    return route.continue()
  })
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } }
  const check = async (what, fn) => { try { await fn() } catch (e) { problems.push(`${what}: ${String(e.message).split('\n')[0]}`) } } // 확인은 서로 막지 않는다(어느 것이 실패하는지 모두 본다)
  const r = await context.request.post(`${base}/api/reset`, { data: { id: PID }, timeout: 30000 }) // 준비 요청: 화면을 기다리는 4초 기본값과 따로(느린 러너)
  if (!r.ok()) problems.push(`reset ${r.status()}`)
  await page.goto(`${base}/#/p/${PID}`)
  await need('문제 제목이 그려진다', () => page.waitForFunction(() => document.getElementById('p-title')?.textContent.trim().length > 0, null, { timeout: 15000 }))
  await need(`${way} 탭에서 튜터 말이 보인다`, async () => {
    if (await page.locator('#problem-peek').isVisible()) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() }
    await page.locator(`#way-tabs [data-way="${way}"]`).click()
    await page.locator('#chat-log .msg.tutor').first().waitFor({ state: 'visible', timeout: 10000 })
  })
  const msg = (id) => page.locator(`#chat-log .msg.tutor[data-msg="${id}"]`)

  await check('꼬리질문 단추·입력 칸이 없다', async () => {
    for (const sel of ['[data-quote]', '#fq-composer', '#fq-text', '#fq-send', '#fq-close', '#fq-quote']) {
      if (await page.locator(sel).count()) throw new Error(`${sel}가 있다`)
    }
    const named = await page.getByRole('button', { name: /꼬리질문/ }).count()
    if (named) throw new Error(`'꼬리질문' 단추 ${named}개`)
    if (await page.locator('#chat-log textarea').count()) throw new Error('대화 칸 안에 입력 칸이 있다')
  })
  await check('블록 번호가 있는 튜터 말마다 표가 하나씩 있고 글이 맞다', async () => {
    if ((await page.locator('#chat-log .block-badge').count()) !== WITH_INDEX.length) throw new Error(`표 ${await page.locator('#chat-log .block-badge').count()}개, 기대 ${WITH_INDEX.length}`)
    for (const id of WITH_INDEX) {
      const badge = msg(id).locator('button.block-badge')
      if ((await badge.count()) !== 1) throw new Error(`${id}: button.block-badge ${await badge.count()}개`)
      const n = EXPECT_NO[id], want = `블록 ${n}/${total} · ${LABEL[KINDS[(n - 1) % 4]]}`
      const got = (await badge.innerText()).replace(/\s+/g, ' ').trim()
      if (got !== want) throw new Error(`${id}: 표 글 ${JSON.stringify(got)}, 기대 ${JSON.stringify(want)}`)
    }
  })
  await check('의자에서 찾기 전 블록의 표에는 이름이 없다', async () => {
    const got = (await msg('m5').locator('.block-badge').innerText())
    if (/시험블록|지금 찾는 블록/.test(got)) throw new Error(`이름이 보인다: ${got}`)
  })
  await check('block_index가 없는 옛 말은 표 없이 그려진다', async () => {
    if (await msg('m6').count() !== 1) throw new Error('옛 말이 그려지지 않았다')
    if (await msg('m6').locator('.block-badge').count()) throw new Error('옛 말에 표가 있다')
    if (!(await msg('m6').innerText()).includes('옛 기록의 말이에요')) throw new Error('옛 말의 글이 없다')
  })
  await check('읽는 글: 튜터 말은 "블록 N에 대한 튜터 말", 표는 "블록 N"으로 읽힌다', async () => {
    for (const id of WITH_INDEX) {
      const n = EXPECT_NO[id]
      const label = await msg(id).getAttribute('aria-label')
      if (label !== `블록 ${n}에 대한 튜터 말`) throw new Error(`${id}: aria-label ${JSON.stringify(label)}`)
      const badge = msg(id).locator('.block-badge')
      const name = ((await badge.getAttribute('aria-label')) || (await badge.innerText())).trim()
      if (!name.startsWith(`블록 ${n}`)) throw new Error(`${id}: 표 이름 ${JSON.stringify(name)}`)
    }
    if (await msg('m6').getAttribute('aria-label') !== null && /^블록 \d/.test(await msg('m6').getAttribute('aria-label'))) throw new Error('옛 말에 블록 번호 aria-label이 붙었다')
  })
  await check('블록이 바뀔 때만 뜨던 구분선이 없다', async () => {
    if (await page.locator('#chat-log .turn').count()) throw new Error('.turn 구분선이 있다')
  })
  await check('옛 꼬리질문 기록이 읽기 전용으로 보이고 거기에 단추가 없다', async () => {
    const text = await page.locator('#chat-log').innerText()
    if (!text.includes(OLD_ASK) || !text.includes(OLD_ANSWER)) throw new Error('옛 꼬리질문 글이 대화에 보이지 않는다')
    const buttons = await page.locator('#chat-log button:not(.block-badge)').count()
    if (buttons) throw new Error(`표 말고 단추 ${buttons}개`)
  })
  await check('표를 누르면 그 블록 칸으로 가고 코드 칸에 초점이 간다', async () => {
    for (const [id, n] of [['m4', 2], ['m1', 1], ['m5', 3]]) {
      await msg(id).locator('.block-badge').click()
      const ok = await page.waitForFunction((n) => {
        const li = document.querySelectorAll('#blocks > li')[n - 1]
        if (!li) return false
        const rect = li.getBoundingClientRect(), a = document.activeElement
        return li.contains(a) && a.tagName === 'TEXTAREA' && rect.bottom > 0 && rect.top < window.innerHeight
      }, n, { timeout: 3000 }).then(() => true, () => false)
      if (!ok) throw new Error(`${id}: 블록 ${n} 칸으로 가지 않았다`)
    }
  })
  await check('키보드로도 누를 수 있다(표는 button이고 Enter로 눌린다)', async () => {
    await page.locator('#blocks > li textarea').first().focus()
    const badge = msg('m4').locator('.block-badge')
    await badge.focus()
    await page.keyboard.press('Enter')
    const ok = await page.waitForFunction(() => document.querySelectorAll('#blocks > li')[1].contains(document.activeElement), null, { timeout: 3000 }).then(() => true, () => false)
    if (!ok) throw new Error('Enter로 블록 2 칸에 가지 않았다')
  })
  await check('화면이 깨지지 않는다(가로로 넘치지 않고 표가 잘리지 않는다)', async () => {
    await page.locator('#chat-log').evaluate((el) => { el.scrollTop = 0 })
    const bad = await page.evaluate(() => {
      const log = document.getElementById('chat-log'), out = []
      if (log.scrollWidth > log.clientWidth + 1) out.push(`대화 칸이 가로로 넘친다 ${log.scrollWidth}>${log.clientWidth}`)
      const box = log.getBoundingClientRect()
      for (const b of log.querySelectorAll('.block-badge')) {
        const r = b.getBoundingClientRect()
        if (!r.width || !r.height) out.push('표가 보이지 않는다')
        else if (r.left < box.left - 1 || r.right > box.right + 1) out.push(`표가 칸 밖으로 나간다 ${Math.round(r.left)}..${Math.round(r.right)} / ${Math.round(box.left)}..${Math.round(box.right)}`)
        if (b.scrollWidth > b.clientWidth + 1) out.push('표 글이 잘린다')
      }
      if (document.documentElement.scrollWidth > window.innerWidth + 1) out.push('쪽이 가로로 넘친다')
      return out
    })
    if (bad.length) throw new Error(bad.join('; '))
  })
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `${tag}.png`) }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.unrouteAll({ behavior: 'ignoreErrors' })
  await context.close()
}

for (const viewport of VIEWPORTS) for (const way of ['chair', 'guide']) await flow(way, viewport)
await browser.close()
process.exit(failed ? 1 : 0)
