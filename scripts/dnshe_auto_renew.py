#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode


DATE_FORMAT = "%Y-%m-%d %H:%M"
DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
)
API_BASE = "https://api005.dnshe.com/index.php?m=domain_hub"

# 显式点名要这些字段：文档说 fields 默认是 all，但同一份文档的返回示例里
# 并没有 expires_at，所以不能指望默认集合一定带上它。
# 文档说明自定义 fields 时接口会自动补充 id，两种情况都能覆盖。
SUBDOMAIN_FIELDS = "id,full_domain,status,created_at,expires_at,never_expires"

# 官方续期窗口在到期前 180 天打开，这里留 5 天余量。
DEFAULT_RENEW_BEFORE_DAYS = 175


@dataclass
class ManagedDomain:
    domain: str
    # never_expires 的域名没有到期日，此时为 None。
    expires_at: datetime | None
    renew_before_days: int
    # 到期时间的取值来源，打进日志便于核对实际走的是哪一级。
    source: str
    never_expires: bool = False

    @property
    def renew_at(self) -> datetime | None:
        if self.expires_at is None:
            return None
        return self.expires_at - timedelta(days=self.renew_before_days)


class DNSHEClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.headers = {
            "X-API-Key": api_key,
            "X-API-Secret": api_secret,
            "Content-Type": "application/json",
            "User-Agent": "dnshe-auto-renew/1.0",
        }

    def _request(self, endpoint: str, action: str, method: str = "GET", payload: Dict[str, Any] | None = None, params: Dict[str, str] | None = None) -> Dict[str, Any]:
        url = f"{API_BASE}&endpoint={endpoint}&action={action}"
        if params:
            url = f"{url}&{urlencode(params)}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, headers=self.headers, data=data, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DNSHE HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"DNSHE network error: {exc}") from exc

    def list_subdomains(self) -> List[Dict[str, Any]]:
        response = self._request("subdomains", "list", params={"fields": SUBDOMAIN_FIELDS})
        if not response.get("success"):
            raise RuntimeError(f"DNSHE list failed: {response}")
        return response.get("subdomains", [])

    def renew_subdomain(self, subdomain_id: int) -> Dict[str, Any]:
        response = self._request(
            "subdomains",
            "renew",
            method="POST",
            payload={"subdomain_id": subdomain_id},
        )
        if not response.get("success"):
            raise RuntimeError(f"DNSHE renew failed: {response}")
        return response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly DNSHE domain renewal helper.")
    parser.add_argument("--state", default="state/domains-state.json", help="Path to state JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate and log actions without renewing.")
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_datetime(value: str) -> datetime:
    cleaned = value.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unsupported datetime format: {value}")


def parse_domain_variable() -> List[str]:
    raw = require_env("DNSHE_DOMAINS")
    domains = [line.strip() for line in raw.splitlines() if line.strip()]
    if not domains:
        raise RuntimeError("DNSHE_DOMAINS is empty.")
    return domains


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"domains": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, raw_state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_subdomain_map(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for item in items:
        full_domain = item.get("full_domain")
        if full_domain:
            mapping[full_domain] = item
    return mapping


def derive_initial_expiration(created_at: str) -> datetime:
    return parse_datetime(created_at) + timedelta(days=365)


def is_truthy(value: Any) -> bool:
    """兼容接口用 true / 1 / "1" / "true" 表达布尔值的写法。"""
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def resolve_expiration(matched: Dict[str, Any], stored_item: Dict[str, Any], domain_name: str) -> Tuple[datetime, str]:
    """按「接口 > 状态文件 > created_at 推算」三级取到期时间。

    接口优先：subdomains/list 本身就会返回 expires_at（官方 V2.0 文档 fields 参数）。
    后两级只是接口不返回该字段时的兜底，避免退回"每周重算、每周续期"的状态。
    """
    api_expires_at = matched.get("expires_at")
    if api_expires_at:
        return parse_datetime(api_expires_at), "api:expires_at"

    stored_expires_at = stored_item.get("expires_at")
    if stored_expires_at:
        return parse_datetime(stored_expires_at), "state:expires_at"

    created_at = matched.get("created_at")
    if not created_at:
        raise RuntimeError(f"DNSHE response missing expires_at and created_at for {domain_name}")
    return derive_initial_expiration(created_at), "derived:created_at_plus_365_days"


def build_managed_domains(domain_names: List[str], subdomain_map: Dict[str, Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[ManagedDomain], bool]:
    managed: List[ManagedDomain] = []
    state_changed = False
    stored_domains = state.setdefault("domains", {})

    for domain_name in domain_names:
        matched = subdomain_map.get(domain_name)
        if not matched:
            raise RuntimeError(f"Domain not found in DNSHE account: {domain_name}")

        item = stored_domains.get(domain_name, {})
        renew_before_days = int(item.get("renew_before_days", DEFAULT_RENEW_BEFORE_DAYS))

        # 永久域名不参与续期，也不写状态。
        if is_truthy(matched.get("never_expires")):
            managed.append(
                ManagedDomain(
                    domain=domain_name,
                    expires_at=None,
                    renew_before_days=renew_before_days,
                    source="api:never_expires",
                    never_expires=True,
                )
            )
            continue

        expires_dt, source = resolve_expiration(matched, item, domain_name)

        # 把解析结果回写状态：接口是权威来源，但万一它哪天不再返回该字段，
        # 状态文件里也有一份真实值兜底，而不是回退到 created_at 推算。
        previous_expires_at = item.get("expires_at")
        previous_renew_before_days = item.get("renew_before_days")
        item["expires_at"] = expires_dt.strftime(DATE_FORMAT)
        item["renew_before_days"] = renew_before_days
        item["source"] = source
        stored_domains[domain_name] = item

        # 只比对到期时间与窗口天数：source 是说明性字段，续期响应与接口
        # 查询写出的取值不同，不该因此多产生一次提交。
        if item["expires_at"] != previous_expires_at or item["renew_before_days"] != previous_renew_before_days:
            state_changed = True

        managed.append(
            ManagedDomain(
                domain=domain_name,
                expires_at=expires_dt,
                renew_before_days=renew_before_days,
                source=source,
            )
        )

    active_domains = set(domain_names)
    stale_domains = [name for name in list(stored_domains.keys()) if name not in active_domains]
    for name in stale_domains:
        del stored_domains[name]
        state_changed = True

    return managed, state_changed


def update_state_expiration(state: Dict[str, Any], domain_name: str, new_expires_at: str) -> bool:
    item = state.setdefault("domains", {}).setdefault(domain_name, {})
    # 统一成 DATE_FORMAT：续期响应带秒，直接落盘会让下次运行读出接口值时
    # 因格式差异被判定为"有变化"，白提交一次。
    canonical = parse_datetime(new_expires_at).strftime(DATE_FORMAT)
    if item.get("expires_at") == canonical:
        return False
    item["expires_at"] = canonical
    item["source"] = "api:renew_response"
    item["renew_before_days"] = int(item.get("renew_before_days", DEFAULT_RENEW_BEFORE_DAYS))
    return True


def main() -> int:
    args = parse_args()
    state_path = Path(args.state).resolve()

    api_key = require_env("DNSHE_API_KEY")
    api_secret = require_env("DNSHE_API_SECRET")
    domain_names = parse_domain_variable()
    client = DNSHEClient(api_key, api_secret)

    now = datetime.now(timezone.utc)
    state = load_state(state_path)
    subdomain_map = find_subdomain_map(client.list_subdomains())
    managed_domains, updated = build_managed_domains(domain_names, subdomain_map, state)

    renewed_count = 0

    print(f"UTC now: {now.strftime(DATE_FORMAT)}")
    for managed in managed_domains:
        matched = subdomain_map[managed.domain]
        # 一并打出接口实际返回的字段名：这是判断 expires_at 到底有没有被返回的
        # 唯一可靠依据，看到这行就不必再额外跑一次调试流程。
        print(f"[SOURCE] {managed.domain} from={managed.source} api_fields={','.join(matched.keys())}")

        if managed.never_expires:
            print(f"[SKIP] {managed.domain} is marked never_expires.")
            continue

        expires_at, renew_at = managed.expires_at, managed.renew_at
        if expires_at is None or renew_at is None:
            print(f"[SKIP] {managed.domain} has no known expiration date.")
            continue

        print(
            f"[CHECK] {managed.domain} expires_at={expires_at.strftime(DATE_FORMAT)} "
            f"renew_at={renew_at.strftime(DATE_FORMAT)}"
        )

        if now < renew_at:
            print(f"[SKIP] {managed.domain} has not entered renewal window yet.")
            continue

        if args.dry_run:
            print(f"[DRY-RUN] Would renew {managed.domain} with subdomain_id={matched['id']}.")
            continue

        result = client.renew_subdomain(int(matched["id"]))
        new_expires_at = result.get("new_expires_at")
        if not new_expires_at:
            raise RuntimeError(f"Renew response missing new_expires_at for {managed.domain}: {result}")

        changed = update_state_expiration(state, managed.domain, new_expires_at)
        updated = updated or changed
        renewed_count += 1
        print(
            f"[RENEWED] {managed.domain} previous_expires_at={result.get('previous_expires_at')} "
            f"new_expires_at={new_expires_at} remaining_days={result.get('remaining_days')}"
        )

    if updated and not args.dry_run:
        save_state(state_path, state)
        print(f"[WRITE] Updated {state_path}")

    if renewed_count == 0:
        print("[DONE] No domains were renewed in this run.")
    else:
        print(f"[DONE] Renewed {renewed_count} domain(s).")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        raise
