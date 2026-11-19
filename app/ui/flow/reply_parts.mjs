// 흐름 시험: 칸이 있는 튜터 말(parts)은 칸으로, 칸이 없는 옛 말은 글로 그려지고, 칸의 단추가 기존 처리기와 같은 일을 한다.
// 쓰는 법: node reply_parts.mjs <주소> <사진 폴더>   (test_flow.py가 서버를 띄운 뒤 부른다)
// 모델은 쓰지 않는다. 문제 상태 응답(/api/state)의 대화·블록·block_facts를 route가 꾸며 주고, 채우기·넘어가기 요청은 받아서 꾸민 응답으로 답한다.
// 정한 이름(구현이 지킬 것):
//   칸이 있는 튜터 말 `.msg.tutor[data-msg]`의 `.bubble` 안에 `.reply-parts` 하나. 그 안에 이 차례로
//   `.slot-result`(결과) → `.slot-question`(질문) → `ul.slot-evidence > li`(근거) → `.slot-buttons > button[data-act]`(fill·skip·run). 빈 칸은 그리지 않는다.
//   머리는 기존 `button.block-badge`로 칸들보다 앞에 있다. 칸 요소마다 aria-label(근거는 목록, 나머지는 role="group"), 결과·질문·근거 칸 안에 작은 표 `.slot-mark`.
//   보이는 글에 칸 이름 낱말(결과·질문·근거)을 쓰지 않는다. 칸이 없는 말(옛 말·사용자 말)에는 `.reply-parts`가 없다.
//   단추: 가장 최근 튜터 말의 단추만 켜지고 앞의 말의 단추는 disabled. fill은 기존 '이 블록 채우기'와 같은 /api/fill 요청,
//   skip은 /api/turn {event:'block_filled', skip:true, quiet:true}, run은 /api/run을 부른다.
//   근거 목록: 말의 note 한 줄, 그리고 가장 최근 튜터 말이 지금 블록(block_facts.index)이면 상태 응답의 block_facts(names·goal)가 더해진다.
import { launch } from '../stageshow/scripts/browser.mjs'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, shots] = process.argv.slice(2)
if (!base || !shots) { console.error('usage: node reply_parts.mjs <url> <screenshot-dir>'); process.exit(2) }
mkdirSync(shots, { recursive: true })

const PID = 'hash_1_popular_shelf'
const VIEWPORTS = [{ width: 1366, height: 689 }, { width: 1093, height: 551 }]
const at = '2026-10-15T00:00:00+09:00'
const svc = (id, text, block_index, parts, move = 'clue') => ({ id, role: 'service', text, at, block_index, move, ...(parts ? { parts } : {}) })
const usr = (id, text, block_index) => ({ id, role: 'user', text, at, block_index, move: null })

const OLD_PARTS = { block_index: 1, result: '아직 넘어가지 않아요. 예시 1에서 `[1, 2]`가 나와야 해요.', question: '`parent[3]`의 값은 얼마인가요?', note: '2번과 3번을 같은 묶음으로 보셨어요.', buttons: ['fill', 'skip'] }
const NEW_PARTS = { block_index: 2, result: '아직 넘어가지 않아요.\n예시 2에서 `[3]`이 나와야 해요.', question: '`total`은 어디서 바뀌나요?', note: '반복마다 더한다고 보셨어요.', buttons: ['fill', 'skip', 'run'] }
const ONLY_TEXT = "이 블록의 힌트는 다 봤어요. 블록 칸에 적어 확인받거나, '이 블록 채우기'로 이 블록만 볼 수 있어요." // 엔진의 HINTS_DONE(tutor/turn/moves.py)
const joined = (p) => [p.result, p.question, p.note].filter(Boolean).join('\n')
const MIXED = [
  svc('m1', '옛 말이에요. 무엇부터 볼까요?', 0, null, 'open'), usr('m2', '입력을 봐요', 0),
  svc('m3', joined(OLD_PARTS), 1, OLD_PARTS), usr('m4', '값은 3이에요', 1),
  svc('m5', joined(NEW_PARTS), 2, NEW_PARTS),
]
const BUTTONS_ONLY = [svc('m1', '옛 말이에요. 무엇부터 볼까요?', 0, null, 'open'), svc('m2', ONLY_TEXT, 2, { block_index: 2, buttons: ['fill'] })]
const LABEL_WORDS = /결과|질문|근거/

const browser = await launch()
let failed = 0

async function flow(way, viewport, scenario) {
  const tag = `reply_parts-${scenario}-${way}-${viewport.width}x${viewport.height}`
  const context = await browser.newContext({ viewport })
  context.setDefaultTimeout(4000)
  const page = await context.newPage()
  const problems = []
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problems.push(`console: ${m.text()}`) })
  const chat = scenario === 'mixed' ? MIXED : BUTTONS_ONLY
  let served = chat // 상태 응답이 줄 대화(튜터가 새 말을 한 것처럼 바꿀 수 있다)
  const facts = scenario === 'mixed' ? { index: 2, names: ['count', 'shelf'], goal: way === 'guide' ? '횟수가 k가 된 순간에 담는다' : '' } : null
  const seen = [] // 화면이 보낸 요청(채우기·턴·실행)
  let blockId = null
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
        s.blocks = s.blocks.map((b, i) => ({ ...b, name: i < 2 || way === 'guide' ? `시험블록${i + 1}` : null }))
        blockId = s.blocks[2].id
        s.open_count = 3
        s.chair = s.guide = served
        s.followups = []
        json.block_facts = facts
      }
      return route.fulfill({ response: res, json })
    }
    if (url.pathname === '/api/fill') {
      seen.push({ path: url.pathname, body: JSON.parse(req.postData() || '{}') })
      return route.fulfill({ json: { block_id: blockId, code: 'count = {}\n', open_count: 3 } })
    }
    if (url.pathname === '/api/turn') {
      const body = JSON.parse(req.postData() || '{}')
      seen.push({ path: url.pathname, body })
      if (body.event === 'block_filled' && body.skip) return route.fulfill({ json: { messages: chat, open_count: 3, renamed: [], withdrawn: [], repeated: false, unsure: false } })
      problems.push(`모델 요청: ${url.pathname} ${body.event}`)
      return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' })
    }
    if (url.pathname === '/api/run') seen.push({ path: url.pathname, body: JSON.parse(req.postData() || '{}') })
    if (/^\/api\/(followup|explain|feedback|debug)$/.test(url.pathname)) { problems.push(`모델 요청: ${url.pathname}`); return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }) }
    return route.continue()
  })
  let stuck = false
  const need = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { stuck = true; problems.push(`${what}: ${String(e.message).split('\n').slice(0, 3).join(' | ')}`) } }
  const check = async (what, fn) => { if (stuck) return; try { await fn() } catch (e) { problems.push(`${what}: ${String(e.message).split('\n').slice(0, 3).join(' | ')}`) } }
  const r = await context.request.post(`${base}/api/reset`, { data: { id: PID }, timeout: 30000 }) // 준비 요청: 화면을 기다리는 4초 기본값과 따로(느린 러너)
  if (!r.ok()) problems.push(`reset ${r.status()}`)
  await page.goto(`${base}/#/p/${PID}`)
  await need('문제 제목이 그려진다', () => page.waitForFunction(() => document.getElementById('p-title')?.textContent.trim().length > 0, null, { timeout: 15000 }))
  await need(`${way} 탭에서 튜터 말이 보인다`, async () => {
    if (await page.locator('#problem-peek').isVisible()) { await page.locator('#problem-peek').click(); await page.locator('#problem-peek').click() }
    await page.locator(`#way-tabs [data-way="${way}"]`).click()
    await page.locator('#chat-log .msg.tutor').last().waitFor({ state: 'visible', timeout: 10000 })
  })
  const msg = (id) => page.locator(`#chat-log .msg.tutor[data-msg="${id}"]`)
  const latest = chat[chat.length - 1].id
  const slots = '.slot-result, .slot-question, ul.slot-evidence, .slot-buttons'
  const settle = () => page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))) // 그리기 두 번(기다림 없이)

  await check('옛 말·사용자 말에는 칸이 없고 글로 그려진다', async () => {
    if (await msg('m1').locator('.reply-parts').count()) throw new Error('옛 말에 .reply-parts가 있다')
    if (!(await msg('m1').innerText()).includes('옛 말이에요')) throw new Error('옛 말의 글이 없다')
    if (await page.locator('#chat-log .msg:not(.tutor) .reply-parts').count()) throw new Error('사용자 말에 .reply-parts가 있다')
  })
  await check('칸이 있는 말은 .bubble 안에 .reply-parts 하나', async () => {
    for (const id of chat.filter((m) => m.parts).map((m) => m.id)) {
      const n = await msg(id).locator('.bubble .reply-parts').count()
      if (n !== 1) throw new Error(`${id}: .bubble .reply-parts ${n}개`)
    }
  })
  await check('칸 요소마다 이름(aria-label)이 있고(근거는 목록, 나머지는 role=group) 칸 이름 낱말이 보이지 않는다', async () => {
    const bad = await page.evaluate(([slotSel, words]) => {
      const out = [], names = new Set()
      for (const el of document.querySelectorAll(`#chat-log .reply-parts :is(${slotSel})`)) {
        const label = (el.getAttribute('aria-label') || '').trim()
        if ((el.tagName === 'UL' ? ![null, 'list'].includes(el.getAttribute('role')) : el.getAttribute('role') !== 'group') || !label) out.push(`${el.className}: role/aria-label 없음`)  // 근거 목록은 목록으로 읽힌다(role이 없거나 list. WebKit은 list-style: none인 목록의 목록 뜻을 빼서 list를 단다)
        names.add(el.className.split(' ')[0] + '|' + label)
      }
      for (const rp of document.querySelectorAll('#chat-log .reply-parts')) if (new RegExp(words).test(rp.innerText)) out.push(`보이는 글에 칸 이름 낱말: ${rp.innerText.slice(0, 60)}`)
      for (const mark of document.querySelectorAll('#chat-log .reply-parts .slot-mark')) if (new RegExp(words).test(mark.textContent)) out.push('작은 표에 칸 이름 낱말')
      return out
    }, [slots, LABEL_WORDS.source])
    if (bad.length) throw new Error(bad.join('; '))
    const marks = await msg(latest).locator('.slot-result .slot-mark, .slot-question .slot-mark, ul.slot-evidence .slot-mark').count()
    if (scenario === 'mixed' ? marks < 3 : !marks) throw new Error(`작은 표 ${marks}개: 있는 칸마다 하나씩 있어야 한다`)
  })

  if (scenario === 'mixed') {
    await check('칸 순서: 머리 → 결과 → 질문 → 근거 → 단추', async () => {
      for (const id of ['m3', 'm5']) {
        const order = await msg(id).evaluate((root) => {
          const pick = (sel) => root.querySelector(sel)
          const list = ['button.block-badge', '.slot-result', '.slot-question', 'ul.slot-evidence', '.slot-buttons'].map(pick)
          if (list.some((el) => !el)) return `칸이 모자란다: ${list.map((el, i) => (el ? '' : i)).join('')}`
          for (let i = 1; i < list.length; i++) if (!(list[i - 1].compareDocumentPosition(list[i]) & Node.DOCUMENT_POSITION_FOLLOWING)) return `순서가 어긋난다: ${i}`
          return ''
        })
        if (order) throw new Error(`${id}: ${order}`)
      }
    })
    await check('칸 글이 맞고 말 글(text)이 되풀이되지 않는다', async () => {
      const got = await msg('m5').locator('.bubble').innerText()
      for (const part of ['예시 2에서', 'total', '반복마다 더한다고']) if (!got.includes(part)) throw new Error(`글이 없다: ${part}`)
      const asked = got.split('은 어디서 바뀌나요').length - 1
      if (asked !== 1) throw new Error(`질문 글이 ${asked}번 보인다`)
      const resultText = (await msg('m5').locator('.slot-result').allInnerTexts()).join('\n')
      if (!resultText.includes('아직 넘어가지 않아요') || !resultText.includes('예시 2에서')) throw new Error(`결과 칸 글: ${JSON.stringify(resultText)}`)
    })
    await check('근거 목록: 지금 말은 되받기·이름(·가이드는 할 일), 앞의 말은 되받기만', async () => {
      const now = await msg('m5').locator('ul.slot-evidence > li').allInnerTexts()
      const old = await msg('m3').locator('ul.slot-evidence > li').allInnerTexts()
      const want = way === 'guide' ? 3 : 2
      if (now.length !== want) throw new Error(`지금 말의 근거 ${now.length}개, 기대 ${want}: ${JSON.stringify(now)}`)
      if (!now[0].includes('반복마다 더한다고')) throw new Error(`첫 근거가 되받기가 아니다: ${now[0]}`)
      if (!(now[1].includes('count') && now[1].includes('shelf'))) throw new Error(`이름이 없다: ${now[1]}`)
      if (way === 'guide' && !now[2].includes('횟수가 k가 된 순간에 담는다')) throw new Error(`할 일이 없다: ${now[2]}`)
      if (old.length !== 1 || !old[0].includes('같은 묶음')) throw new Error(`앞의 말의 근거: ${JSON.stringify(old)}`)
    })
    await check('단추: 글이 할 일을 말하고, 지금 말만 켜지고 앞의 말은 disabled', async () => {
      const now = await msg('m5').locator('.slot-buttons > button[data-act]').evaluateAll((els) => els.map((el) => ({ act: el.dataset.act, text: el.textContent.trim(), off: el.disabled })))
      if (now.map((b) => b.act).join() !== 'fill,skip,run') throw new Error(`지금 말의 단추 ${JSON.stringify(now)}`)
      if (now.some((b) => b.off)) throw new Error('지금 말의 단추가 꺼져 있다')
      if (now.some((b) => !b.text || b.text === b.act || !/[가-힣]/.test(b.text)) || new Set(now.map((b) => b.text)).size !== 3) throw new Error(`단추 글 ${JSON.stringify(now)}`)
      const old = await msg('m3').locator('.slot-buttons > button[data-act]').evaluateAll((els) => els.map((el) => ({ act: el.dataset.act, off: el.disabled })))
      if (old.map((b) => b.act).join() !== 'fill,skip' || old.some((b) => !b.off)) throw new Error(`앞의 말의 단추 ${JSON.stringify(old)}`)
    })
    await check('앞의 말의 단추를 눌러도 아무 요청이 가지 않는다', async () => {
      await msg('m3').locator('.slot-buttons > button[data-act]').evaluateAll((els) => els.forEach((el) => el.click()))
      await settle()
      if (seen.length) throw new Error(`요청 ${JSON.stringify(seen.map((q) => q.path))}`)
    })
  } else {
    await check('단추만 있는 말: 글을 결과 자리에 한 번 보이고 단추가 켜져 있다. 빈 칸은 없다', async () => {
      const got = await msg('m2').locator('.bubble').innerText()
      if (got.split(ONLY_TEXT).length - 1 !== 1) throw new Error(`글이 ${got.split(ONLY_TEXT).length - 1}번 보인다: ${JSON.stringify(got)}`)
      if (!(await msg('m2').locator('.slot-result').innerText()).includes(ONLY_TEXT)) throw new Error('결과 칸에 글이 없다')
      for (const sel of ['.slot-question', '.slot-evidence']) if (await msg('m2').locator(sel).count()) throw new Error(`빈 칸 ${sel}를 그렸다`)
      const buttons = await msg('m2').locator('.slot-buttons > button[data-act]').evaluateAll((els) => els.map((el) => [el.dataset.act, el.disabled]))
      if (JSON.stringify(buttons) !== '[["fill",false]]') throw new Error(`단추 ${JSON.stringify(buttons)}`)
    })
  }

  await check('화면이 깨지지 않는다(가로로 넘치지 않고 칸이 말풍선 밖으로 나가지 않는다)', async () => {
    const bad = await page.evaluate(() => {
      const log = document.getElementById('chat-log'), out = []
      if (log.scrollWidth > log.clientWidth + 1) out.push(`대화 칸이 가로로 넘친다 ${log.scrollWidth}>${log.clientWidth}`)
      for (const rp of log.querySelectorAll('.reply-parts')) {
        const box = rp.closest('.bubble').getBoundingClientRect()
        for (const el of rp.querySelectorAll('*')) {
          const r = el.getBoundingClientRect()
          if (r.width && r.right > box.right + 1) out.push(`${el.className || el.tagName}가 말풍선 밖으로 나간다 ${Math.round(r.right)}>${Math.round(box.right)}`)
        }
      }
      if (document.documentElement.scrollWidth > window.innerWidth + 1) out.push('쪽이 가로로 넘친다')
      return out
    })
    if (bad.length) throw new Error(bad.slice(0, 3).join('; '))
  })

  const btn = (act) => msg(latest).locator(`.slot-buttons > button[data-act="${act}"]`)
  const confirmFill = async () => { if (await page.locator('[data-fill-yes]').count()) await page.locator('[data-fill-yes]').first().click() } // 칸에 적은 것이 있거나 의자에서 찾기 전이면 먼저 묻는다
  const waitReq = (path) => { const got = page.waitForRequest((q) => new URL(q.url()).pathname === path && q.method() === 'POST'); got.catch(() => {}); return got }
  await check('fill 단추는 기존 "이 블록 채우기"와 같은 /api/fill 요청을 보낸다', async () => {
    const first = waitReq('/api/fill')
    await page.locator(`[data-fill="${blockId}"]`).click()
    await confirmFill()
    const was = JSON.parse((await first).postData())
    const second = waitReq('/api/fill')
    await btn('fill').click()
    await confirmFill()
    const now = JSON.parse((await second).postData())
    if (was.block_id !== blockId || JSON.stringify(now) !== JSON.stringify(was)) throw new Error(`기존 ${JSON.stringify(was)} / 단추 ${JSON.stringify(now)}`)
  })
  if (scenario === 'mixed') {
    await check('skip 단추는 기존 넘어가기와 같은 요청(block_filled, skip)을 보낸다', async () => {
      const got = waitReq('/api/turn')
      await btn('skip').click()
      const body = JSON.parse((await got).postData())
      if (body.event !== 'block_filled' || body.skip !== true || body.quiet !== true || body.block_id !== blockId || body.mode !== way || body.code !== 'count = {}\n') throw new Error(JSON.stringify(body))
    })
    await check('run 단추는 기존 실행(/api/run)을 부른다', async () => {
      for (const ta of await page.locator('#blocks > li textarea').all()) if (!(await ta.inputValue()).trim()) await ta.fill('x = 1\n')
      const got = waitReq('/api/run')
      await btn('run').click()
      if (await page.locator('#code-yes').isVisible()) await page.locator('#code-yes').click() // 코드 전체에 적은 것이 있어 바꿀지 묻는다
      const body = JSON.parse((await got).postData())
      if (body.id !== PID || typeof body.code !== 'string') throw new Error(JSON.stringify(body))
    })
    await check('키보드(Enter)로 누른 단추는 대화를 다시 그린 뒤에도 초점이 가장 최근 튜터 말의 같은 단추나 그 블록 칸에 남는다', async () => {
      served = [...chat, svc('m7', '새 결과 줄이에요.', 2, { block_index: 2, result: '새 결과 줄이에요.', buttons: ['fill', 'skip'] })]
      await btn('skip').focus()
      await page.keyboard.press('Enter')
      await msg('m7').waitFor({ state: 'visible' })
      await page.waitForFunction(() => document.activeElement && document.activeElement !== document.body, null, { timeout: 2000 })
      const at = await page.evaluate(() => { const a = document.activeElement, m = a.closest('.msg'); return { tag: a.tagName, id: a.id, act: a.dataset.act, msg: m && m.dataset.msg, block: a.dataset.block } })
      if (!((at.act === 'skip' && at.msg === 'm7') || at.block === blockId)) throw new Error(`초점이 ${JSON.stringify(at)}에 있다`)
    })
  }
  if (problems.length) {
    failed++
    await page.screenshot({ path: join(shots, `${tag}.png`) }).catch(() => {})
    console.error(`FAIL ${tag}\n  - ${problems.join('\n  - ')}`)
  } else console.log(`ok ${tag}`)
  await page.unrouteAll({ behavior: 'ignoreErrors' })
  await context.close()
}

for (const viewport of VIEWPORTS) for (const way of ['chair', 'guide']) for (const scenario of ['mixed', 'buttons']) await flow(way, viewport, scenario)
await browser.close()
process.exit(failed ? 1 : 0)
