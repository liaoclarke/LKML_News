#!/usr/bin/env python3
"""
LKML ARM64 Tracker - IMAP email filter, analyzer, and publisher.

Every 10 minutes:
1. Fetch new emails from 163.com IMAP
2. Filter emails addressed to ARM kernel maintainers -> move to arm64 folder
3. Analyze new arm64 emails using LLM (topic, participants, conclusions, next steps)
4. Write analysis to ~/workspace/lkml/<series_name>.md
5. Git commit and push to GitHub
"""

import email
import email.utils
import hashlib
import json
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from email.header import decode_header
from email.policy import default

# ============================================================
# CONFIGURATION
# ============================================================

IMAP_HOST = "imap.163.com"
IMAP_PORT = 993
IMAP_USER = "imagent4bd@163.com"
IMAP_PASS = "YVx9ZbUg23KY2i8F"
ARM64_FOLDER = "arm64"

TARGET_RECIPIENTS = [
    "catalin.marinas@arm.com",
    "guohanjun@huawei.com",
    "will@kernel.org",
    "mark.rutland@arm.com",
    "maz@kernel.org",
    "james.morse@arm.com",
]

LKML_DIR = os.path.expanduser("~/workspace/lkml")
STATE_FILE = os.path.expanduser("~/.lkml_tracker_state.json")

# Anthropic-compatible API (DeepSeek)
LLM_API_URL = "https://api.deepseek.com/anthropic/v1/messages"
LLM_API_KEY = os.environ.get(
    "ANTHROPIC_AUTH_TOKEN",
    "sk-91d3fbdc36dc4a38bc2df3642c53f5a7",
)
LLM_MODEL = os.environ.get("ANTHROPIC_MODEL", "deepseek-v4-pro")

LOG_FILE = os.path.join(LKML_DIR, "lkml_tracker.log")
ERROR_LOG_FILE = os.path.join(LKML_DIR, "lkml_tracker_error.log")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def log_error(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ============================================================
# IMAP CLIENT (raw socket)
# ============================================================

class IMAPClient:
    def __init__(self, host, port, timeout=30):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        ctx = ssl.create_default_context()
        self.sock = ctx.wrap_socket(self.sock, server_hostname=host)
        self.rfile = self.sock.makefile("rb")
        self._readline()  # consume banner
        self.counter = 0
        self.logged_in = False

    def _readline(self):
        line = self.rfile.readline()
        if not line:
            return None
        return line.decode("utf-8", errors="replace").rstrip("\r\n")

    def _next_tag(self):
        self.counter += 1
        return f"A{self.counter:04d}"

    def _cmd(self, command):
        tag = self._next_tag()
        self.sock.sendall(f"{tag} {command}\r\n".encode())

        responses = []
        while True:
            line = self._readline()
            if line is None:
                break
            responses.append(line)
            if line.startswith(tag + " "):
                break
            # Handle BYE (server disconnecting)
            if line.startswith("* BYE"):
                break
        return tag, responses

    def login(self, user, password):
        tag, resp = self._cmd(f"LOGIN {user} {password}")
        if resp and "OK" in resp[-1]:
            self.logged_in = True
            return True
        log_error(f"IMAP LOGIN failed: {resp[-1] if resp else 'no response'}")
        return False

    def send_id(self):
        try:
            self._cmd('ID ("name" "NeoMutt" "version" "20260504")')
        except Exception as e:
            log(f"  send_id failed (non-fatal): {e}")

    def select(self, folder, readonly=False):
        cmd = "EXAMINE" if readonly else "SELECT"
        tag, resp = self._cmd(f'{cmd} "{folder}"')
        for r in resp:
            if tag in r and "OK" in r:
                return resp
        return None

    def search(self, criteria, uid=False):
        """SEARCH or UID SEARCH. Returns all matching IDs across all continuation lines."""
        prefix = "UID SEARCH" if uid else "SEARCH"
        _, resp = self._cmd(f"{prefix} {criteria}")
        results = []
        for line in resp:
            if "* SEARCH" in line:
                parts = line.split()
                if len(parts) > 2:
                    results.extend(parts[2:])
        return results

    def fetch_full(self, uid_set, use_uid=True):
        """Fetch full RFC822 emails. Returns list of (id, raw_bytes)."""
        uid_str = ",".join(str(u) for u in uid_set) if isinstance(uid_set, (list, tuple)) else str(uid_set)
        prefix = "UID FETCH" if use_uid else "FETCH"
        tag = self._next_tag()
        self.sock.sendall(f"{tag} {prefix} {uid_str} (RFC822)\r\n".encode())

        results = []
        while True:
            line = self._readline()
            if line is None or line.startswith(tag + " ") or line.startswith("* BYE"):
                break
            if "FETCH" in line and "{" in line:
                # Extract UID from response line like: * 1 FETCH (UID 123 RFC822 {size}
                uid = "?"
                m = re.search(r'UID (\d+)', line)
                if m:
                    uid = m.group(1)
                idx = line.rfind("{")
                idx2 = line.rfind("}")
                if idx >= 0 and idx2 > idx:
                    try:
                        size = int(line[idx+1:idx2])
                        raw = self.rfile.read(size)
                        self.rfile.readline()  # consume )\r\n after literal
                        results.append((uid, raw))
                    except (ValueError, socket.error) as e:
                        log_error(f"  fetch_full error for {uid}: {e}")

        return results

    def copy(self, uid_set, folder):
        uid_str = ",".join(str(u) for u in uid_set) if isinstance(uid_set, (list, tuple)) else str(uid_set)
        tag = self._next_tag()
        self.sock.sendall(f'{tag} UID COPY {uid_str} "{folder}"\r\n'.encode())
        while True:
            line = self._readline()
            if line is None or line.startswith(tag + " ") or line.startswith("* BYE"):
                return line and "OK" in line if line else False

    def store(self, uid_set, flags):
        uid_str = ",".join(str(u) for u in uid_set) if isinstance(uid_set, (list, tuple)) else str(uid_set)
        tag = self._next_tag()
        self.sock.sendall(f"{tag} UID STORE {uid_str} {flags}\r\n".encode())
        while True:
            line = self._readline()
            if line is None or line.startswith(tag + " ") or line.startswith("* BYE"):
                return line and "OK" in line if line else False

    def expunge(self):
        tag = self._next_tag()
        self.sock.sendall(f"{tag} EXPUNGE\r\n".encode())
        while True:
            line = self._readline()
            if line is None or line.startswith(tag + " ") or line.startswith("* BYE"):
                break

    def logout(self):
        if self.sock:
            try:
                tag = self._next_tag()
                self.sock.sendall(f"{tag} LOGOUT\r\n".encode())
                while True:
                    line = self._readline()
                    if line is None or line.startswith(tag + " ") or line.startswith("* BYE"):
                        break
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass

    def ensure_arm64_folder(self):
        """Check if arm64 folder exists, create if not."""
        if self.select(ARM64_FOLDER, readonly=True) is None:
            log("  Creating arm64 folder...")
            self._cmd(f'CREATE "{ARM64_FOLDER}"')


# ============================================================
# UTILITIES
# ============================================================

def decode_mime_header(value):
    if value is None:
        return ""
    parts = decode_header(value)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)


def get_email_date(msg):
    date_str = msg.get("Date", "")
    if date_str:
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            pass
    return None


def get_header(msg, name):
    return decode_mime_header(msg.get(name, ""))


def addresses_from_header(msg, header_name):
    raw = get_header(msg, header_name)
    if not raw:
        return []
    addrs = []
    for name, addr in email.utils.getaddresses([raw]):
        if addr:
            addrs.append(addr.lower())
    return addrs


def extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(charset, errors="replace")
                except Exception:
                    pass
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors="replace")
        except Exception:
            pass
    return body.strip()


def strip_patch_prefix(subject):
    s = re.sub(r'^\[?Re:\s*', '', subject, flags=re.IGNORECASE).strip()
    s = re.sub(r'^\[?Fwd?:\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\[PATCH[^\]]*\]\s*', '', s, flags=re.IGNORECASE).strip()
    return s


def series_name(subject):
    name = strip_patch_prefix(subject)
    name = re.sub(r'\s+\d+/\d+\s*$', '', name).strip()
    return name


def filename_from_series(name):
    safe = re.sub(r'[^\w\-]+', '_', name)
    safe = safe.strip("_")
    if not safe or len(safe) < 3:
        safe = "unknown_series"
    return safe + ".md"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_check": None, "processed_uids": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ============================================================
# EMAIL FILTERING
# ============================================================

def is_arm_related(msg):
    all_addrs = set()
    for header in ("To", "Cc"):
        all_addrs.update(addresses_from_header(msg, header))
    for target in TARGET_RECIPIENTS:
        if target.lower() in all_addrs:
            return True
    return False


# ============================================================
# LLM ANALYSIS
# ============================================================

def build_analysis_prompt(thread_emails):
    MAX_CHARS = 8000
    email_texts = []
    total_chars = 0

    emails_sorted = sorted(
        thread_emails, key=lambda e: get_email_date(e) or datetime.min
    )

    for msg in emails_sorted:
        sender = get_header(msg, "From")
        date = get_header(msg, "Date")
        subject = get_header(msg, "Subject")
        body = extract_body(msg)
        if len(body) > 2000:
            body = body[:2000] + "\n[...truncated...]"

        text = f"---\nFrom: {sender}\nDate: {date}\nSubject: {subject}\n\n{body}"
        if total_chars + len(text) > MAX_CHARS:
            break
        email_texts.append(text)
        total_chars += len(text)

    combined = "\n".join(email_texts)

    prompt = f"""You are analyzing Linux kernel mailing list discussions about ARM64 architecture.

Below are emails from a discussion thread. Please analyze them and respond in Chinese.

REQUIRED OUTPUT FORMAT (use this exact structure):

## 核心话题
[Detailed discussion of the core topic. Extract key technical points, quote important fragments from the emails. Be thorough - at least 200-300 words describing what the patch/discussion is about, the technical motivation, and the key arguments]

## 参与讨论人员
[List names and affiliations of all participants in this thread]

## 达成的结论
[Whether consensus was reached. If yes, describe the conclusion. If not, describe the outstanding disagreements]

## 下一步改进方向
[What needs to happen next. Specific code changes, further discussion needed, testing requirements, etc.]

## 新增补丁
[If new patch versions were posted in this thread, list them with version numbers and brief changes]

---

EMAIL THREAD:
{combined}
"""
    return prompt


def call_llm(prompt):
    data = json.dumps({
        "model": LLM_MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    for attempt in range(3):
        try:
            req = urllib.request.Request(LLM_API_URL, data=data, headers={
                "Content-Type": "application/json",
                "x-api-key": LLM_API_KEY,
                "anthropic-version": "2023-06-01",
            })
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read().decode())
            content = result.get("content", [])
            if isinstance(content, list) and content:
                text = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text += block.get("text", "")
                return text
            elif isinstance(content, str):
                return content
            return ""
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                return f"[LLM API Error: {e}]"


# ============================================================
# FILE OPERATIONS
# ============================================================

def write_analysis(series_name_str, analysis_text, thread_date):
    filepath = os.path.join(LKML_DIR, filename_from_series(series_name_str))

    ts = thread_date.strftime("%Y-%m-%d %H:%M UTC") if thread_date else "Unknown"
    section_header = f"\n---\n\n## 更新 - {ts}\n\n"
    content = section_header + analysis_text + "\n"

    if os.path.exists(filepath):
        with open(filepath, "a") as f:
            f.write(content)
    else:
        header = f"# {series_name_str}\n"
        with open(filepath, "w") as f:
            f.write(header + content)

    return filepath


def git_commit_and_push():
    try:
        os.chdir(LKML_DIR)
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, timeout=30
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            capture_output=True, timeout=30
        )
        if result.returncode != 0:
            stderr = result.stderr.decode()[:200] if result.stderr else ""
            # "nothing to commit" is not an error
            if "nothing to commit" not in stderr and "nothing added to commit" not in stderr:
                log_error(f"  Git commit failed: {stderr}")
                return False

        push = subprocess.run(
            ["git", "push"],
            capture_output=True, timeout=60
        )
        if push.returncode == 0:
            return True
        else:
            err = push.stderr.decode()[:200] if push.stderr else "unknown"
            log_error(f"  Git push failed: {err}")
            return False
    except Exception as e:
        log_error(f"  Git error: {e}")
        return False


# ============================================================
# MAIN LOGIC
# ============================================================

def run_once():
    state = load_state()
    last_check = state.get("last_check")
    if last_check:
        last_check_date = datetime.fromisoformat(last_check)
        since = last_check_date - timedelta(hours=1)  # 1h overlap to avoid misses
        log(f"Last check: {last_check_date}, searching since {since}")
    else:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        log(f"First run - checking last 1 hour")

    processed_uids = set(state.get("processed_uids", []))
    now = datetime.now(timezone.utc)
    new_processing = False

    conn = None
    try:
        conn = IMAPClient(IMAP_HOST, IMAP_PORT)

        if not conn.login(IMAP_USER, IMAP_PASS):
            log_error("Login failed - credentials may be expired or incorrect")
            return

        try:
            conn.send_id()
        except Exception:
            pass  # Non-fatal

        conn.ensure_arm64_folder()

        # ---- Step 1 & 2: Fetch new emails, filter by ARM recipients, move to arm64 ----
        date_str = since.strftime("%d-%b-%Y")
        conn.select("INBOX", readonly=True)
        all_uids = conn.search(f"SINCE {date_str}", uid=True)
        log(f"  Found {len(all_uids)} emails in INBOX since {date_str}")

        arm_uids = []
        if all_uids:
            for i in range(0, len(all_uids), 10):
                chunk = all_uids[i:i+10]
                raw_emails = conn.fetch_full(chunk, use_uid=True)
                for uid, raw in raw_emails:
                    try:
                        msg = email.message_from_bytes(raw, policy=default)
                        if is_arm_related(msg):
                            arm_uids.append(uid)
                    except Exception as e:
                        log_error(f"  Error parsing uid {uid}: {e}")

        if arm_uids:
            conn.select("INBOX", readonly=False)
            for i in range(0, len(arm_uids), 10):
                batch = arm_uids[i:i+10]
                conn.copy(batch, ARM64_FOLDER)
                conn.store(batch, "+FLAGS (\\Deleted)")
            conn.expunge()
            log(f"  Moved {len(arm_uids)} ARM-related emails to arm64 folder")
        else:
            log("  No ARM-related emails found")

        # ---- Step 3 & 4: Analyze new arm64 emails ----
        arm64_uids = conn.search("1:*", uid=True) if conn.select(ARM64_FOLDER, readonly=True) else []
        arm64_uid_set = set(arm64_uids)

        new_arm64_uids = [u for u in arm64_uids if u not in processed_uids]
        log(f"  Arm64 folder: {len(arm64_uids)} total, {len(new_arm64_uids)} new")

        if new_arm64_uids:
            # Build UID -> message mapping
            uid_to_msg = {}
            for i in range(0, len(new_arm64_uids), 10):
                chunk = new_arm64_uids[i:i+10]
                raw_emails = conn.fetch_full(chunk, use_uid=True)
                for uid, raw in raw_emails:
                    try:
                        msg = email.message_from_bytes(raw, policy=default)
                        uid_to_msg[uid] = msg
                    except Exception as e:
                        log_error(f"  Error parsing uid {uid}: {e}")

            # Group by series name
            threads = {}
            for uid, msg in uid_to_msg.items():
                subject = get_header(msg, "Subject")
                sn = series_name(subject)
                if sn not in threads:
                    threads[sn] = {"uids": [], "msgs": []}
                threads[sn]["uids"].append(uid)
                threads[sn]["msgs"].append(msg)

            for sn, data in threads.items():
                msgs = data["msgs"]
                log(f"  Analyzing: {sn} ({len(msgs)} msgs)")
                prompt = build_analysis_prompt(msgs)
                analysis = call_llm(prompt)

                if analysis and not analysis.startswith("[LLM API Error"):
                    max_date = max(
                        (get_email_date(m) or datetime.min for m in msgs)
                    )
                    filepath = write_analysis(sn, analysis, max_date)
                    log(f"  Wrote: {filepath}")
                    new_processing = True
                else:
                    log_error(f"  Analysis failed for: {sn}")

                # Save state incrementally after each thread
                for u in data["uids"]:
                    processed_uids.add(u)
                state["processed_uids"] = list(processed_uids)
                save_state(state)

    except Exception as e:
        log_error(f"  Connection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            try:
                conn.logout()
            except Exception:
                pass

    # ---- Update state ----
    state["last_check"] = now.isoformat()
    if len(processed_uids) > 5000:
        processed_uids = set(list(processed_uids)[-5000:])
    state["processed_uids"] = list(processed_uids)
    save_state(state)

    # ---- Step 5: Git push ----
    if new_processing:
        if git_commit_and_push():
            log("  Git push successful")

    log("Done.")


def main_loop(interval=600):
    """Run the tracker every `interval` seconds (default: 10 minutes)."""
    running = True

    def handle_signal(sig, frame):
        nonlocal running
        log(f"Received signal {sig}, shutting down...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log(f"LKML ARM64 Tracker starting (interval={interval}s)")

    while running:
        try:
            run_once()
        except Exception as e:
            log_error(f"Unexpected error in run_once: {e}")

        if not running:
            break

        # Sleep in 10-second increments to allow responsive shutdown
        elapsed = 0
        while elapsed < interval and running:
            time.sleep(min(10, interval - elapsed))
            elapsed += 10


def main():
    if "--once" in sys.argv:
        run_once()
    else:
        main_loop()


if __name__ == "__main__":
    main()
