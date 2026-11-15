"""ChatGPT 요금제 로그인(Sign in with ChatGPT) 시험. 네트워크 없이 인가 주소, 콜백, ID 토큰 검증, 저장, 갱신, 요청 모양, 스트림을 본다.
서명 시험의 RSA 키는 여기서 만든다(1024비트: 시험을 빨리 돌리려고 작게)."""

import base64
import hashlib
import json
import os
import random
import stat
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from ..llm.client import _backend_session

_backend_session()  # 저장소 루트를 경로에 더해 app.llm을 부른다
from app.llm.errors import LlmFailed, LlmNotConfigured  # noqa: E402
from app.llm.openai.oauth import chat, idtoken, pkce, token  # noqa: E402
from app.llm.parse import text_of  # noqa: E402
from app.llm.wire import set_transport  # noqa: E402

PLAN = "chatgpt.tokens.use.direct email offline_access openid profile resource.invoke"


def _prime(bits: int, rng: random.Random) -> int:
    while True:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if all(n % p for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31)) and all(_mr(n, rng.randrange(2, n - 1)) for _ in range(20)):
            return n


def _mr(n: int, a: int) -> bool:
    d, r = n - 1, 0
    while d % 2 == 0:
        d, r = d // 2, r + 1
    x = pow(a, d, n)
    if x in (1, n - 1):
        return True
    for _ in range(r - 1):
        x = pow(x, 2, n)
        if x == n - 1:
            return True
    return False


def _keypair(seed: int) -> tuple[int, int, int]:
    rng, e = random.Random(seed), 65537
    while True:
        p, q = _prime(512, rng), _prime(512, rng)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e:
            return p * q, e, pow(e, -1, phi)


N, E, D = _keypair(7)
N2, E2, D2 = _keypair(11)  # 다른 키(틀린 서명)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _jwt(claims: dict, *, kid="k1", n=N, d=D, alg="RS256") -> str:
    signed = f"{_b64(json.dumps({'alg': alg, 'kid': kid}).encode())}.{_b64(json.dumps(claims).encode())}"
    size = (n.bit_length() + 7) // 8
    tail = idtoken.SHA256_INFO + hashlib.sha256(signed.encode()).digest()
    em = b"\x00\x01" + b"\xff" * (size - len(tail) - 3) + b"\x00" + tail
    return f"{signed}.{_b64(pow(int.from_bytes(em, 'big'), d, n).to_bytes(size, 'big'))}"


def _claims(**over) -> dict:
    now = int(time.time())
    return {"iss": "https://auth.openai.com", "sub": "user-1", "aud": ["oaiapp_one"], "nonce": "n1", "email": "user@example.com",
            "iat": now, "exp": now + 3600, **over}


JWKS = {"keys": [{"kty": "RSA", "kid": "k1", "use": "sig", "alg": "RS256", "n": _b64(N.to_bytes(128, "big")), "e": _b64(E.to_bytes(3, "big"))}]}


class IdTokenTest(unittest.TestCase):
    def setUp(self):
        idtoken._keys.clear()

    def verify(self, jwt, client="oaiapp_one", nonce="n1"):
        return idtoken.verify(jwt, client_id=client, nonce=nonce, fetch=lambda: JWKS)

    def test_good_signature_passes(self):
        self.assertEqual(self.verify(_jwt(_claims()))["sub"], "user-1")
        self.assertEqual(self.verify(_jwt(_claims(aud="oaiapp_one")))["sub"], "user-1")  # aud가 글 하나여도 된다

    def test_rejects(self):
        cases = {
            "다른 키의 서명": _jwt(_claims(), n=N2, d=D2),
            "바꾼 본문": (lambda t: t.split(".")[0] + "." + _b64(json.dumps(_claims(sub="other")).encode()) + "." + t.split(".")[2])(_jwt(_claims())),
            "다른 aud": _jwt(_claims(aud=["oaiapp_two"])),
            "만료": _jwt(_claims(exp=int(time.time()) - 60)),
            "다른 발급자": _jwt(_claims(iss="https://example.com")),
            "모르는 kid": _jwt(_claims(), kid="k9"),
            "서명 방식 none": _jwt(_claims(), alg="none"),
            "aud 여럿에 azp 없음": _jwt(_claims(aud=["oaiapp_one", "oaiapp_two"])),
            "sub 없음": _jwt({k: v for k, v in _claims().items() if k != "sub"}),
            "모양": "a.b",
        }
        for name, jwt in cases.items():
            with self.subTest(name), self.assertRaises(LlmFailed):
                self.verify(jwt)
        with self.assertRaises(LlmFailed):  # nonce 다름
            self.verify(_jwt(_claims()), nonce="n2")
        with self.assertRaises(LlmFailed):  # 빈 nonce를 기대하면 받지 않는다
            self.verify(_jwt(_claims(nonce="")), nonce="")

    def test_unknown_kid_refetches_once(self):
        calls = []
        self.assertEqual(idtoken.verify(_jwt(_claims()), client_id="oaiapp_one", nonce="n1", fetch=lambda: calls.append(1) or JWKS)["sub"], "user-1")
        idtoken.verify(_jwt(_claims()), client_id="oaiapp_one", nonce="n1", fetch=lambda: calls.append(1) or JWKS)
        self.assertEqual(len(calls), 1)  # 아는 kid는 다시 받지 않는다


SSE = "\n".join([
    'event: response.created',
    'data: {"type": "response.created", "response": {}}',
    '',
    'data: {"type": "response.output_text.delta", "delta": "안"}',
    'data: {"type": "response.output_text.delta", "delta": "녕"}',
    'data: {"type": "response.completed", "response": {"usage": {"input_tokens": 5, "output_tokens": 2}}}',
])


class PlanLoginTest(unittest.TestCase):
    def assert_private(self, path):
        """로그인 파일은 자료 폴더 안에만 생기고, POSIX에서는 권한이 0600이다.
        Windows에는 POSIX 권한 비트가 없어(늘 0o666으로 읽힌다) 권한은 보지 않는다. 사용자 폴더의 기본 권한에 기댄다."""
        self.assertTrue(path.is_file())
        self.assertTrue(path.resolve().is_relative_to(Path(self.dir.name).resolve()), path)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"ALGOBLOCK_LLM_AUTH_DIR": self.dir.name})
        self.env.start()
        self.port = mock.patch.object(token, "PORT", 0)
        self.port.start()
        idtoken._keys.clear()
        idtoken._keys["k1"] = (N, E)
        self.forms = []

    def tearDown(self):
        set_transport(None)
        token._stop()
        token._login["error"] = None
        idtoken._keys.clear()
        self.port.stop()
        self.env.stop()
        self.dir.cleanup()

    def fake_token(self, scope=PLAN, client="oaiapp_one", sub="user-1"):
        def fake(form):
            self.forms.append(form)
            return {"access_token": "at", "refresh_token": "r1", "id_token": _jwt(_claims(aud=[client], sub=sub, nonce=self.nonce)),
                    "token_type": "Bearer", "expires_in": 3600, "scope": scope}
        return fake

    def start(self):
        started = token.begin_login(timeout=10)
        query = {k: v[0] for k, v in parse_qs(urlsplit(started["url"]).query).items()}
        self.nonce = query["nonce"]
        return started, query

    def callback(self, query, **params):
        url = f"{query['redirect_uri']}?" + "&".join(f"{k}={v}" for k, v in params.items())
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")

    def test_first_registration_url(self):
        started, q = self.start()
        self.assertTrue(started["url"].startswith("https://auth.openai.com/api/accounts/authorize?"))
        self.assertEqual(q["client_id"], "dynamic_agent_client")
        self.assertEqual(q["agent_name_hint"], "AlgoBlock")
        self.assertTrue(q["ext_agent_host_id"].startswith("urn:uuid:"))
        self.assertEqual(q["response_type"], "code")
        self.assertRegex(q["redirect_uri"], r"^http://127\.0\.0\.1:\d+/auth/callback$")
        self.assertEqual(q["scope"], "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct")
        self.assertEqual(q["resource"], "https://api.openai.com/v1")
        self.assertEqual(q["code_challenge_method"], "S256")
        self.assertNotIn("=", q["code_challenge"])
        for absent in ("id_token_hint", "login_hint", "prompt"):
            self.assertNotIn(absent, q)
        _, again = self.start()
        self.assertEqual(again["ext_agent_host_id"], q["ext_agent_host_id"])  # 기기 아이디는 다시 쓴다
        self.assertNotEqual((again["state"], again["nonce"], again["code_challenge"]), (q["state"], q["nonce"], q["code_challenge"]))  # 시도마다 새로
        self.assert_private(token.auth_dir() / "chatgpt-host.json")

    def test_callback_end_to_end_then_reauth_uses_issued_client(self):
        with mock.patch.object(token, "_token", self.fake_token()):
            _, q = self.start()
            status, page = self.callback(q, code="c1", state=q["state"], client_id="oaiapp_one", scope="x")
        self.assertEqual(status, 200, page)
        self.assertIn("연결됐어요", page)
        self.assertEqual(token.login_status(), {"connected": True, "error": None})
        form = self.forms[0]
        self.assertEqual((form["grant_type"], form["client_id"], form["code"], form["redirect_uri"], form["resource"]),
                         ("authorization_code", "oaiapp_one", "c1", q["redirect_uri"], "https://api.openai.com/v1"))
        self.assertEqual(base64.urlsafe_b64encode(hashlib.sha256(form["code_verifier"].encode()).digest()).decode().rstrip("="), q["code_challenge"])
        saved = json.loads(token.token_path().read_text())
        self.assert_private(token.token_path())
        self.assertEqual((saved["client_id"], saved["subject"], saved["email"], saved["ext_agent_host_id"]), ("oaiapp_one", "user-1", "user@example.com", q["ext_agent_host_id"]))
        self.assertIn("chatgpt.tokens.use.direct", saved["scopes"])
        for _ in range(50):  # 리스너가 스스로 닫힌다
            if token._login["server"] is None:
                break
            time.sleep(0.05)
        self.assertIsNone(token._login["server"])
        _, again = self.start()  # 다시 로그인: 발급 client_id와 힌트, agent_name_hint 없음
        self.assertEqual(again["client_id"], "oaiapp_one")
        self.assertNotIn("agent_name_hint", again)
        self.assertEqual(again["login_hint"], "user@example.com")
        self.assertEqual(again["id_token_hint"], saved["id_token"])
        self.assertEqual(again["ext_agent_host_id"], q["ext_agent_host_id"])
        self.assertNotIn("prompt", again)

    def test_wrong_state_is_ignored_and_listener_stays(self):
        _, q = self.start()
        status, _ = self.callback(q, code="c1", state="other", client_id="oaiapp_one")
        self.assertEqual(status, 404)
        self.assertIsNotNone(token._login["server"])

    def test_access_denied_stops_without_exchange(self):
        with mock.patch.object(token, "_token", self.fake_token()):
            _, q = self.start()
            status, page = self.callback(q, error="access_denied", state=q["state"])
        self.assertEqual(status, 400)
        self.assertEqual(self.forms, [])
        self.assertFalse(token.login_status()["connected"])
        self.assertIn("허락하지 않아", token.login_status()["error"])
        self.assertIn("워크스페이스나 플랜", token.login_status()["error"])  # 동의 화면에서 막혀 취소한 경우도 알린다

    def test_refused_code_mentions_plan(self):
        """코드 교환이 invalid_grant로 끝나면 코드가 지났을 수도, 플랜 때문에 막혔을 수도 있다고 함께 알린다."""
        def refuse(form):
            raise token.Refused("invalid_grant", 400)
        with mock.patch.object(token, "_token", refuse):
            _, q = self.start()
            self.callback(q, code="c", state=q["state"], client_id="issued-client")
        error = token.login_status()["error"]
        self.assertFalse(token.login_status()["connected"])
        self.assertIn("로그인 코드가 지났다면", error)
        self.assertIn("워크스페이스나 플랜", error)

    def test_new_registration_without_issued_client_is_incomplete(self):
        with mock.patch.object(token, "_token", self.fake_token()):
            for given in ("", "dynamic_agent_client"):
                _, q = self.start()
                self.callback(q, code="c1", state=q["state"], **({"client_id": given} if given else {}))
                self.assertIn("등록이 끝나지 않았어요", token.login_status()["error"])
        self.assertEqual(self.forms, [])

    def test_reauth_rejects_other_client_and_other_account(self):
        token._write(token.token_path(), {"client_id": "oaiapp_one", "subject": "user-1", "refresh_token": "r", "scopes": PLAN.split()})
        with mock.patch.object(token, "_token", self.fake_token()):
            _, q = self.start()
            self.callback(q, code="c1", state=q["state"], client_id="oaiapp_two")
            self.assertIn("다른 등록", token.login_status()["error"])
        self.assertEqual(self.forms, [])
        with mock.patch.object(token, "_token", self.fake_token(sub="user-2")):
            _, q = self.start()
            self.callback(q, code="c1", state=q["state"])  # 다시 로그인은 client_id를 빼도 된다
            self.assertIn("계정과 달라요", token.login_status()["error"])
        self.assertEqual(json.loads(token.token_path().read_text())["subject"], "user-1")  # 기록을 바꾸지 않았다

    def test_without_plan_scope_keeps_sign_in_but_not_connected(self):
        with mock.patch.object(token, "_token", self.fake_token(scope="email offline_access openid profile")):
            _, q = self.start()
            status, page = self.callback(q, code="c1", state=q["state"], client_id="oaiapp_one")
        self.assertEqual(status, 200)
        self.assertIn("허락하지 않아", page)
        self.assertEqual(token.login_status(), {"connected": False, "error": token.NO_PLAN})
        with self.assertRaises(LlmNotConfigured):
            token.access_token()
        _, again = self.start()  # 다시 허락을 묻는다(같은 client_id, 범위 전체, prompt=consent)
        self.assertEqual((again["client_id"], again["prompt"]), ("oaiapp_one", "consent"))
        self.assertIn("chatgpt.tokens.use.direct", again["scope"])

    def test_old_token_file_is_not_read(self):
        (token.auth_dir() / "openai-oauth.json").write_text('{"access_token": "old"}')
        self.assertEqual(token.login_status(), {"connected": False, "error": token.OLD})
        with self.assertRaises(LlmNotConfigured):
            token.access_token()
        self.assertTrue((token.auth_dir() / "openai-oauth.json").exists())  # 지우지 않는다

    def saved(self, **over):
        record = {"client_id": "oaiapp_one", "subject": "user-1", "id_token": "idt", "access_token": "at", "refresh_token": "r1",
                  "expires_in": 3600, "scopes": PLAN.split(), "saved_at": "2020-01-01T00:00:00+00:00", **over}
        token._write(token.token_path(), record)

    def test_refresh_near_expiry(self):
        self.saved()
        fake = lambda form: self.forms.append(form) or {"access_token": "at2", "refresh_token": "r2", "expires_in": 3600, "scope": PLAN}
        with mock.patch.object(token, "_token", fake):
            self.assertEqual(token.access_token(), "at2")
            self.assertEqual(token.access_token(), "at2")  # 새 토큰은 아직 살아 있다
        self.assertEqual(len(self.forms), 1)
        self.assertEqual(self.forms[0], {"grant_type": "refresh_token", "client_id": "oaiapp_one", "refresh_token": "r1", "resource": "https://api.openai.com/v1"})
        saved = json.loads(token.token_path().read_text())
        self.assertEqual((saved["refresh_token"], saved["id_token"]), ("r2", "idt"))

    def test_dead_refresh_clears_tokens(self):
        self.saved()

        def dead(form):
            raise token.Refused("refresh_token_reused", 400)

        with mock.patch.object(token, "_token", dead), self.assertRaises(LlmNotConfigured):
            token.access_token()
        saved = json.loads(token.token_path().read_text())
        self.assertEqual((saved["access_token"], saved["refresh_token"], saved["client_id"]), ("", "", "oaiapp_one"))
        self.assertEqual(token.login_status(), {"connected": False, "error": token.RELOGIN})

    def test_chat_request_shape_and_stream(self):
        self.saved(saved_at="2999-01-01T00:00:00+00:00")
        seen = {}

        def transport(url, headers, body, timeout):
            seen.update(url=url, headers=headers, body=body)
            return SSE

        set_transport(transport)
        got = chat.complete("gpt-6.1-sol", [{"role": "system", "content": "규칙"}, {"role": "user", "content": "가"}],
                            params={"cache_key": "k1", "effort": "low", "max_tokens": 10, "temperature": 0})
        self.assertEqual(seen["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(seen["headers"]["Authorization"], "Bearer at")
        self.assertEqual(set(seen["headers"]), {"Authorization", "Content-Type", "Accept"})
        body = seen["body"]
        self.assertIs(body["store"], False)
        self.assertIs(body["stream"], True)
        self.assertEqual((body["prompt_cache_key"], body["reasoning"]), ("k1", {"effort": "low"}))
        self.assertEqual([row["role"] for row in body["input"]], ["developer", "user"])
        for absent in ("temperature", "max_output_tokens", "previous_response_id", "metadata"):
            self.assertNotIn(absent, body)
        self.assertEqual((text_of(got), got["usage"]["output_tokens"]), ("안녕", 2))

    def test_stream_errors(self):
        self.saved(saved_at="2999-01-01T00:00:00+00:00")
        with self.assertRaises(LlmFailed):
            chat.read_sse(['data: {"type": "response.output_text.delta", "delta": "x"}'])  # completed 없이 끝남
        with self.assertRaises(LlmFailed):
            chat.read_sse(['data: {"type": "response.incomplete", "response": {"incomplete_details": {"reason": "max_output_tokens"}}}'])
        limit = 'data: {"type": "response.failed", "response": {"error": {"code": "subscription_sharing_usage_limit_exceeded"}}}'
        with mock.patch("sys.stderr"), self.assertRaises(LlmFailed) as caught:
            chat.read_sse([limit])
        self.assertIn("chatgpt.com/settings/usage", str(caught.exception))
        self.assertTrue(str(caught.exception).endswith("(429)"))
        self.assertTrue(token.login_status()["connected"])  # 한도는 연결을 끊지 않는다
        with mock.patch("sys.stderr"):
            self.assertIsInstance(chat.refused(403, b'{"error": {"code": "subscription_sharing_user_not_eligible"}}'), LlmNotConfigured)
        self.assertEqual(token.login_status(), {"connected": False, "error": chat.NOT_ELIGIBLE})

    def test_refused_before_stream(self):
        self.saved(saved_at="2999-01-01T00:00:00+00:00")
        with mock.patch("sys.stderr"):
            self.assertEqual(str(chat.refused(503, b'{"detail": "x"}')), chat.UNAVAILABLE)
            self.assertNotRegex(str(chat.refused(400, b'{"error": {"code": "subscription_sharing_unsupported_capability", "param": "tools"}}')), r"\(\d{3}\)")
            self.assertTrue(token.login_status()["connected"])
            self.assertIsInstance(chat.refused(401, b'{"detail": "no"}'), LlmNotConfigured)
        self.assertEqual(token.login_status(), {"connected": False, "error": token.RELOGIN})

    def test_models_lists_visible_slugs(self):
        self.saved(saved_at="2999-01-01T00:00:00+00:00")
        seen = {}

        def transport(url, headers, body, timeout):
            seen.update(url=url, body=body)
            return {"models": [{"slug": "gpt-6.1-sol", "visibility": "list"}, {"slug": "hidden", "visibility": "hide"}, {"slug": "gpt-6-luna", "visibility": "list"}]}

        set_transport(transport)
        self.assertEqual(chat.models(), ["gpt-6.1-sol", "gpt-6-luna"])
        self.assertEqual((seen["url"], seen["body"]), ("https://api.openai.com/v1/models", None))

    def test_no_borrowed_client_or_private_backend(self):
        folder = os.path.dirname(token.__file__)
        for name in os.listdir(folder):
            if name.endswith(".py"):
                text = Path(folder, name).read_text(encoding="utf-8")
                self.assertNotIn("backend-api", text, name)
                self.assertNotIn("originator", text, name)
        self.assertEqual(pkce.REGISTER_CLIENT, "dynamic_agent_client")


if __name__ == "__main__":
    unittest.main()
