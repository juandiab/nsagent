import json
from contextlib import asynccontextmanager
from typing import Any

import httpx

NEXTGEN_API_PREFIX = "/mgmt/api/nextgen/v1"


def normalize_host(host: str) -> str:
    cleaned = host.strip()
    for prefix in ("https://", "http://"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned.split("/")[0]


class NextGenClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        timeout: float = 20.0,
        verify_ssl: bool = False,
    ):
        self.host = normalize_host(host)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{self.host}{NEXTGEN_API_PREFIX}"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "NextGenClient":
        self._client = httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout)
        await self.login()
        return self

    async def __aexit__(self, *_args: Any) -> None:
        await self.logout()
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def login(self) -> None:
        if self._client is None:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._client.post(
            f"{self.base_url}/login",
            json={"login": {"username": self.username, "password": self.password}},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        if response.status_code != 200:
            message = _extract_error_message(response)
            if response.status_code in {401, 403}:
                raise ValueError("Authentication failed — invalid username or password")
            raise ValueError(message or f"Next-Gen API login failed with HTTP {response.status_code}")

        if not _has_session_cookie(response):
            raise ValueError("Next-Gen API login succeeded but no sessionid cookie was returned")

    async def logout(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.post(
                f"{self.base_url}/logout",
                headers={"Accept": "application/json"},
            )
        except Exception:
            pass

    async def get(self, path: str) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._client.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Accept": "application/json"},
        )
        if response.status_code != 200:
            message = _extract_error_message(response)
            raise ValueError(message or f"Request failed with HTTP {response.status_code}")
        return response.json()

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._client.post(
            f"{self.base_url}/{path.lstrip('/')}",
            json=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text.strip()}

        if response.status_code not in (200, 201):
            message = _extract_error_message(response)
            if isinstance(payload, dict) and not message:
                message = str(payload.get("errormessage") or payload.get("message") or payload)
            raise ValueError(message or f"Request failed with HTTP {response.status_code}")
        if isinstance(payload, dict) and payload.get("success") is False:
            message = str(payload.get("message") or payload.get("errormessage") or "Next-Gen API request failed")
            raise ValueError(message)
        return payload if isinstance(payload, dict) else {"result": payload}

    async def put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._client.put(
            f"{self.base_url}/{path.lstrip('/')}",
            json=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text.strip()}

        if response.status_code not in (200, 201, 204):
            message = _extract_error_message(response)
            if isinstance(payload, dict) and not message:
                message = str(payload.get("errormessage") or payload.get("message") or payload)
            raise ValueError(message or f"Request failed with HTTP {response.status_code}")
        if isinstance(payload, dict) and payload.get("success") is False:
            message = str(payload.get("message") or payload.get("errormessage") or "Next-Gen API request failed")
            raise ValueError(message)
        return payload if isinstance(payload, dict) else {"result": payload}

    async def delete(self, path: str) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._client.delete(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Accept": "application/json"},
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text.strip()} if response.text.strip() else {}

        if response.status_code not in (200, 202, 204):
            message = _extract_error_message(response)
            if isinstance(payload, dict) and not message:
                message = str(payload.get("errormessage") or payload.get("message") or payload)
            raise ValueError(message or f"Request failed with HTTP {response.status_code}")
        return payload if isinstance(payload, dict) else {"result": payload}

    async def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        verb = (method or "GET").strip().upper()
        if verb == "GET":
            return await self.get(path)
        if verb == "POST":
            return await self.post(path, body or {})
        if verb == "PUT":
            return await self.put(path, body or {})
        if verb == "DELETE":
            return await self.delete(path)
        raise ValueError(f"Unsupported HTTP method: {method} (use GET, POST, PUT, or DELETE)")

    async def create_application(
        self,
        name: str,
        virtual_ip: str,
        port: int,
        protocol: str,
        servers: list[str],
        *,
        servers_port: int | None = None,
        servers_protocol: str | None = None,
    ) -> dict[str, Any]:
        cleaned_name = name.strip()
        cleaned_ip = virtual_ip.strip()
        if not cleaned_name:
            raise ValueError("application name is required")
        if not _looks_like_ip(cleaned_ip):
            raise ValueError(f"Invalid virtual_ip: {virtual_ip}")
        if not servers:
            raise ValueError("At least one backend server IP is required")

        backend_port = servers_port if servers_port is not None else port
        backend_protocol = (servers_protocol or protocol).strip().upper()
        app_protocol = protocol.strip().upper()

        body = {
            "application": {
                "name": cleaned_name,
                "virtual_ip": cleaned_ip,
                "port": int(port),
                "protocol": app_protocol,
                "servers_port": int(backend_port),
                "servers_protocol": backend_protocol,
                "servers": [server.strip() for server in servers if server.strip()],
            }
        }
        payload = await self.post("applications", body)
        return {
            "success": True,
            "transport": "Next-Gen API",
            "operation": "POST /applications",
            "application": body["application"],
            "response": payload,
        }

    async def list_virtual_servers(self) -> dict[str, Any]:
        nextgen_apps = await self.get_applications()
        virtual_servers: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for item in nextgen_apps:
            normalized = _normalize_application(item)
            normalized["source"] = "nextgen:application"
            normalized["type"] = "nextgen"
            name = normalized.get("name", "")
            if name:
                seen_names.add(name.lower())
            virtual_servers.append(normalized)

        nitro_vservers = await _fetch_nitro_lbvservers(
            self._client,
            self.host,
            self.username,
            self.password,
        )
        classic_count = 0
        for item in nitro_vservers:
            name = str(item.get("name") or "")
            if name.lower() in seen_names:
                continue
            virtual_servers.append(item)
            classic_count += 1

        return {
            "virtualServerCount": len(virtual_servers),
            "nextGenCount": len(nextgen_apps),
            "classicCount": classic_count,
            "virtualServers": virtual_servers,
        }

    async def get_applications(self) -> list[dict[str, Any]]:
        payload = await self.get("applications")
        return _extract_resource_list(payload, "application", "applications")

    async def list_virtual_ips(self) -> list[dict[str, Any]]:
        applications = await self.get_applications()
        virtual_ips: list[dict[str, Any]] = []
        seen: set[str] = set()

        for application in applications:
            app_name = application.get("name", "")
            for vip_entry in _extract_virtual_ips_from_application(application, app_name):
                key = f"{vip_entry['virtualIp']}:{vip_entry.get('port', '')}:{vip_entry.get('application', '')}"
                if key in seen:
                    continue
                seen.add(key)
                virtual_ips.append(vip_entry)

            if not app_name:
                continue

            try:
                detail = await self.get(f"applications/{app_name}")
            except Exception:
                continue

            app_detail = detail.get("application", detail)
            if isinstance(app_detail, dict):
                for vip_entry in _extract_virtual_ips_from_application(app_detail, app_name):
                    key = f"{vip_entry['virtualIp']}:{vip_entry.get('port', '')}:{vip_entry.get('application', '')}"
                    if key in seen:
                        continue
                    seen.add(key)
                    virtual_ips.append(vip_entry)

        return virtual_ips

    async def list_ip_addresses(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        sources_used: set[str] = set()

        def add_entry(
            ip_address: str,
            ip_type: str,
            source: str,
            *,
            name: str = "",
            port: str | int = "",
            application: str = "",
            state: str = "",
        ) -> None:
            cleaned = str(ip_address or "").strip()
            if not cleaned or cleaned in {"0.0.0.0", "*"}:
                return
            normalized_type = ip_type or "IP"
            key = f"{cleaned}:{normalized_type}"
            if key in seen:
                for entry in entries:
                    if entry["ipAddress"] == cleaned and entry["type"] == normalized_type:
                        if name and not entry.get("name"):
                            entry["name"] = name
                        if port and not entry.get("port"):
                            entry["port"] = port
                        if application and not entry.get("application"):
                            entry["application"] = application
                        if state and not entry.get("state"):
                            entry["state"] = state
                        if source not in entry.get("source", ""):
                            entry["source"] = f"{entry['source']}, {source}" if entry.get("source") else source
                return
            seen.add(key)
            sources_used.add(source)
            entries.append(
                {
                    "ipAddress": cleaned,
                    "type": normalized_type,
                    "source": source,
                    "name": name,
                    "port": port,
                    "application": application,
                    "state": state,
                }
            )

        applications = await self.get_applications()
        for application in applications:
            app_name = str(application.get("name") or "")
            for vip_entry in _extract_virtual_ips_from_application(application, app_name):
                add_entry(
                    vip_entry["virtualIp"],
                    "VIP",
                    f"nextgen:{vip_entry.get('source', 'application')}",
                    name=str(vip_entry.get("frontend") or app_name),
                    port=vip_entry.get("port") or "",
                    application=app_name,
                )

            if not app_name:
                continue

            try:
                detail = await self.get(f"applications/{app_name}")
            except Exception:
                continue

            app_detail = detail.get("application", detail)
            if isinstance(app_detail, dict):
                for vip_entry in _extract_virtual_ips_from_application(app_detail, app_name):
                    add_entry(
                        vip_entry["virtualIp"],
                        "VIP",
                        f"nextgen:{vip_entry.get('source', 'application')}",
                        name=str(vip_entry.get("frontend") or app_name),
                        port=vip_entry.get("port") or "",
                        application=app_name,
                    )

                for server_ip in _extract_server_ips_from_application(app_detail):
                    add_entry(server_ip, "Server", "nextgen:backend", application=app_name)

        try:
            config_sets_payload = await self.get("config_sets")
            config_sets = _extract_resource_list(config_sets_payload, "config_set", "config_sets")
            for config_set in config_sets:
                config_name = str(config_set.get("name") or "")
                for ip_value, ip_type, label in _extract_ips_from_object(config_set, "config_set"):
                    add_entry(ip_value, ip_type, "nextgen:config_set", name=label or config_name)

                if not config_name:
                    continue

                try:
                    config_payload = await self.get(f"config_sets/{config_name}/config")
                except Exception:
                    continue

                for ip_value, ip_type, label in _extract_ips_from_object(config_payload, "config_set_config"):
                    add_entry(ip_value, ip_type, "nextgen:config_set", name=label or config_name)
        except Exception:
            pass

        nextgen_ip_count = len(entries)
        nitro_nsip = await _fetch_nitro_nsip_addresses(
            self._client,
            self.host,
            self.username,
            self.password,
        )
        for item in nitro_nsip:
            add_entry(
                item["ipAddress"],
                item["type"],
                "nitro:nsip",
                state=item.get("state", ""),
            )

        nitro_vservers = await _fetch_nitro_lbvserver_addresses(
            self._client,
            self.host,
            self.username,
            self.password,
        )
        for item in nitro_vservers:
            add_entry(
                item["ipAddress"],
                "VIP",
                "nitro:lbvserver",
                name=item.get("name", ""),
                port=item.get("port", ""),
                state=item.get("state", ""),
            )

        return {
            "managementIp": self.host,
            "ipCount": len(entries),
            "nextGenIpCount": nextgen_ip_count,
            "addresses": entries,
            "sources": sorted(sources_used),
            "note": (
                "Next-Gen API lists IPs from applications and config_sets. "
                "Classic NSIP/SNIP/VIP and lbvserver addresses are included via read-only NITRO when needed."
            ),
        }

    async def get_system_info(self) -> dict[str, Any]:
        applications = await self.get_applications()
        platform = await _fetch_appliance_platform_stats(
            self._client,
            self.host,
            self.username,
            self.password,
        )
        version = platform.get("version", "")
        info: dict[str, Any] = {
            "host": self.host,
            "managementIp": self.host,
            "api": "NetScaler Next-Gen API",
            "apiPath": NEXTGEN_API_PREFIX,
            "authenticatedUser": self.username,
            "applicationCount": len(applications),
            "nextGenApiAvailable": True,
            **platform,
            "firmwareVersion": version,
        }
        if not info.get("ipAddress"):
            info["ipAddress"] = self.host
        return info

    async def get_resource(self, path: str) -> dict[str, Any]:
        return await self.get(path)


async def _fetch_appliance_platform_stats(
    client: httpx.AsyncClient | None,
    host: str,
    username: str,
    password: str,
) -> dict[str, Any]:
    """Read-only firmware/version metadata — not exposed by the Next-Gen API."""
    if client is None:
        return {"platformStatsAvailable": False}

    best: dict[str, Any] = {"platformStatsAvailable": False}
    base_url = f"https://{host}/nitro/v1"
    session_token: str | None = None

    header_headers = {
        "Accept": "application/json",
        "X-NITRO-USER": username,
        "X-NITRO-PASS": password,
    }

    try:
        for path, resource_key in (
            ("stat/ns", "ns"),
            ("config/ns", "ns"),
            ("config/nsversion", "nsversion"),
            ("config/systemparameter", "systemparameter"),
        ):
            merged = await _fetch_nitro_resource(client, f"{base_url}/{path}", header_headers, resource_key)
            best = _merge_platform_info(best, merged)

        login_response = await client.post(
            f"{base_url}/config/login",
            json={"login": {"username": username, "password": password}},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        login_payload = login_response.json()
        if login_response.status_code == 200 and login_payload.get("errorcode", 0) == 0:
            session_token = (login_payload.get("login") or {}).get("sessionid")
            if session_token:
                auth_headers = {
                    "Accept": "application/json",
                    "Cookie": f"NITRO_AUTH_TOKEN={session_token}",
                }
                for path, resource_key in (
                    ("stat/ns", "ns"),
                    ("config/ns", "ns"),
                    ("config/nsversion", "nsversion"),
                ):
                    merged = await _fetch_nitro_resource(client, f"{base_url}/{path}", auth_headers, resource_key)
                    best = _merge_platform_info(best, merged)
    except Exception:
        return best
    finally:
        if session_token:
            try:
                await client.post(
                    f"{base_url}/config/logout",
                    json={"logout": {}},
                    headers={
                        "Content-Type": "application/json",
                        "Cookie": f"NITRO_AUTH_TOKEN={session_token}",
                    },
                )
            except Exception:
                pass

    return best


async def _fetch_nitro_resource(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    resource_key: str,
) -> dict[str, Any]:
    try:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"platformStatsAvailable": False}

        payload = response.json()
        if payload.get("errorcode", 0) != 0:
            return {"platformStatsAvailable": False}

        entries = payload.get(resource_key, [])
        if not entries:
            return {"platformStatsAvailable": False}

        info = entries[0] if isinstance(entries, list) else entries
        if not isinstance(info, dict):
            return {"platformStatsAvailable": False}

        return _normalize_ns_platform_info(info)
    except Exception:
        return {"platformStatsAvailable": False}


def _merge_platform_info(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current)
    for key, value in incoming.items():
        if key == "platformStatsAvailable":
            merged[key] = bool(current.get(key)) or bool(value)
            continue
        if value and not merged.get(key):
            merged[key] = value
    merged["platformStatsAvailable"] = any(
        merged.get(field)
        for field in (
            "hostname",
            "version",
            "buildNumber",
            "serialNumber",
            "ipAddress",
            "mode",
            "platform",
        )
    )
    return merged


def _normalize_ns_platform_info(info: dict[str, Any]) -> dict[str, Any]:
    lower_map = {str(key).lower(): value for key, value in info.items() if value not in (None, "")}

    def pick(*keys: str) -> str:
        for key in keys:
            value = lower_map.get(key.lower())
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    normalized = {
        "hostname": pick("hostname", "host_name", "systemname", "system_name"),
        "version": pick(
            "version",
            "product_version",
            "productversion",
            "softwareversion",
            "software_version",
            "nsversion",
        ),
        "buildNumber": pick("build_number", "buildnumber", "product_build_number", "build"),
        "serialNumber": pick("serialnumber", "serial_number", "serial"),
        "ipAddress": pick("ipaddress", "ip_address", "host", "nsip"),
        "mode": pick("mode", "ha_state", "hastate", "ha_mode"),
        "platform": pick("platform", "platformtype", "platform_type", "machine"),
    }

    has_data = any(normalized.values())
    return {
        "platformStatsAvailable": has_data,
        **normalized,
    }


def _extract_virtual_ips_from_application(application: dict[str, Any], app_name: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def add_vip(source: str, virtual_ip: str, protocol: str = "", port: str | int = "", frontend: str = "") -> None:
        if not virtual_ip:
            return
        entries.append(
            {
                "application": app_name,
                "frontend": frontend,
                "virtualIp": virtual_ip,
                "protocol": protocol,
                "port": port,
                "source": source,
            }
        )

    add_vip(
        "application",
        str(application.get("virtual_ip") or application.get("virtualIp") or ""),
        str(application.get("protocol") or ""),
        application.get("port") or "",
    )

    frontends = application.get("frontends", [])
    if isinstance(frontends, list):
        for frontend in frontends:
            if not isinstance(frontend, dict):
                continue
            add_vip(
                "frontend",
                str(frontend.get("virtual_ip") or frontend.get("virtualIp") or ""),
                str(frontend.get("protocol") or application.get("protocol") or ""),
                frontend.get("port") or application.get("port") or "",
                str(frontend.get("name") or ""),
            )

    listeners = application.get("listeners", [])
    if isinstance(listeners, list):
        for listener in listeners:
            if not isinstance(listener, dict):
                continue
            add_vip(
                "listener",
                str(application.get("virtual_ip") or application.get("virtualIp") or ""),
                str(listener.get("protocol") or application.get("protocol") or ""),
                listener.get("port") or application.get("port") or "",
                str(listener.get("name") or ""),
            )

    return entries


_IP_FIELD_HINTS = (
    "ipaddress",
    "ip_address",
    "ipv46",
    "virtual_ip",
    "virtualip",
    "primaryipaddress",
    "primary_ip_address",
)


def _looks_like_ip(value: str) -> bool:
    cleaned = value.strip()
    if not cleaned or cleaned in {"0.0.0.0", "*"}:
        return False
    if cleaned.count(".") == 3:
        parts = cleaned.split(".")
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
    return ":" in cleaned


def _infer_ip_type_from_key(key: str, fallback: str = "IP") -> str:
    lowered = key.lower()
    if "nsip" in lowered:
        return "NSIP"
    if "snip" in lowered:
        return "SNIP"
    if "vip" in lowered or "vserver" in lowered or "frontend" in lowered:
        return "VIP"
    if "server" in lowered:
        return "Server"
    return fallback


def _extract_ips_from_object(payload: Any, label_prefix: str = "") -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []

    def walk(node: Any, name_hint: str = "") -> None:
        if isinstance(node, dict):
            current_name = str(node.get("name") or name_hint or "")
            for key, value in node.items():
                key_lower = str(key).lower()
                if isinstance(value, str) and any(hint in key_lower for hint in _IP_FIELD_HINTS):
                    if _looks_like_ip(value):
                        found.append((value.strip(), _infer_ip_type_from_key(key_lower), current_name or label_prefix))
                elif isinstance(value, (dict, list)):
                    walk(value, current_name)
        elif isinstance(node, list):
            for item in node:
                walk(item, name_hint)

    walk(payload)
    return found


def _extract_server_ips_from_application(application: dict[str, Any]) -> list[str]:
    servers: list[str] = []
    for key in ("servers", "backends"):
        value = application.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and _looks_like_ip(item):
                    servers.append(item.strip())
                elif isinstance(item, dict):
                    for ip_value, _, _ in _extract_ips_from_object(item, "server"):
                        servers.append(ip_value)
        elif isinstance(value, dict):
            for item in value.values():
                if isinstance(item, str) and _looks_like_ip(item):
                    servers.append(item.strip())
                elif isinstance(item, dict):
                    for ip_value, _, _ in _extract_ips_from_object(item, "server"):
                        servers.append(ip_value)
    return servers


async def _fetch_nitro_nsip_addresses(
    client: httpx.AsyncClient | None,
    host: str,
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    if client is None:
        return []

    headers = {
        "Accept": "application/json",
        "X-NITRO-USER": username,
        "X-NITRO-PASS": password,
    }
    try:
        response = await client.get(f"https://{host}/nitro/v1/config/nsip", headers=headers)
        payload = response.json()
    except Exception:
        return []

    if payload.get("errorcode", 0) != 0:
        return []

    rows: list[dict[str, Any]] = []
    for item in payload.get("nsip", []) or []:
        if not isinstance(item, dict):
            continue
        ip_address = str(item.get("ipaddress") or "").strip()
        if not ip_address:
            continue
        ip_type = str(item.get("type") or (item.get("iptype") or ["IP"])[0] or "IP")
        rows.append(
            {
                "ipAddress": ip_address,
                "type": ip_type,
                "state": str(item.get("state") or ""),
            }
        )
    return rows


async def _fetch_nitro_lbvserver_addresses(
    client: httpx.AsyncClient | None,
    host: str,
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    if client is None:
        return []

    headers = {
        "Accept": "application/json",
        "X-NITRO-USER": username,
        "X-NITRO-PASS": password,
    }
    try:
        response = await client.get(f"https://{host}/nitro/v1/config/lbvserver", headers=headers)
        payload = response.json()
    except Exception:
        return []

    if payload.get("errorcode", 0) != 0:
        return []

    rows: list[dict[str, Any]] = []
    for item in payload.get("lbvserver", []) or []:
        if not isinstance(item, dict):
            continue
        ip_address = str(item.get("ipv46") or item.get("ipaddress") or "").strip()
        if not _looks_like_ip(ip_address):
            continue
        rows.append(
            {
                "ipAddress": ip_address,
                "name": str(item.get("name") or ""),
                "port": item.get("port") or "",
                "state": str(item.get("curstate") or item.get("state") or ""),
            }
        )
    return rows


async def _fetch_nitro_lbvservers(
    client: httpx.AsyncClient | None,
    host: str,
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    if client is None:
        return []

    headers = {
        "Accept": "application/json",
        "X-NITRO-USER": username,
        "X-NITRO-PASS": password,
    }
    try:
        response = await client.get(f"https://{host}/nitro/v1/config/lbvserver", headers=headers)
        payload = response.json()
    except Exception:
        return []

    if payload.get("errorcode", 0) != 0:
        return []

    rows: list[dict[str, Any]] = []
    for item in payload.get("lbvserver", []) or []:
        if not isinstance(item, dict):
            continue
        ip_address = str(item.get("ipv46") or item.get("ipaddress") or "").strip()
        rows.append(
            {
                "name": str(item.get("name") or ""),
                "virtualIp": ip_address,
                "port": item.get("port") or "",
                "protocol": str(item.get("servicetype") or ""),
                "state": str(item.get("curstate") or item.get("state") or ""),
                "source": "nitro:lbvserver",
                "type": "classic",
            }
        )
    return rows


def _has_session_cookie(response: httpx.Response) -> bool:
    if response.cookies.get("sessionid"):
        return True
    set_cookie = response.headers.get("set-cookie", "")
    return "sessionid=" in set_cookie.lower()


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()

    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if isinstance(payload.get("error"), dict):
            nested = payload["error"].get("message")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return response.text.strip()


def _extract_resource_list(payload: Any, singular_key: str, plural_key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    if isinstance(payload.get(plural_key), list):
        return [item for item in payload[plural_key] if isinstance(item, dict)]

    resource = payload.get(singular_key)
    if isinstance(resource, dict):
        return [resource]
    if isinstance(resource, list):
        return [item for item in resource if isinstance(item, dict)]

    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get(plural_key), list):
        return [item for item in data[plural_key] if isinstance(item, dict)]

    return []


def _normalize_application(item: dict[str, Any]) -> dict[str, Any]:
    servers = item.get("servers", [])
    if isinstance(servers, dict):
        servers = list(servers.values())

    return {
        "name": item.get("name", ""),
        "virtualIp": item.get("virtual_ip", item.get("virtualIp", "")),
        "protocol": item.get("protocol", ""),
        "port": item.get("port", ""),
        "servers": servers if isinstance(servers, list) else [],
        "serverCount": len(servers) if isinstance(servers, list) else 0,
        "defaultCertificateRef": item.get("default_certificate_ref", ""),
        "state": item.get("state", item.get("status", "")),
    }


@asynccontextmanager
async def nextgen_session(host: str, username: str, password: str):
    from app.services.config_service import get_runtime_config

    config = get_runtime_config()
    async with NextGenClient(
        host,
        username,
        password,
        timeout=float(config.nitro_timeout_seconds),
        verify_ssl=config.verify_ssl,
    ) as client:
        yield client


async def test_appliance_connection(host: str, username: str, password: str) -> tuple[bool, str]:
    if not host or not username or not password:
        return False, "Host, username, and password are required"

    normalized_host = normalize_host(host)
    try:
        async with nextgen_session(host, username, password):
            return True, f"Successfully authenticated to {normalized_host} via NetScaler Next-Gen API"
    except httpx.ConnectError:
        return False, (
            f"Could not connect to {normalized_host} — check hostname/IP, HTTPS (port 443), "
            "and that Next-Gen API is enabled (`enable ns nextgenapi`)"
        )
    except httpx.TimeoutException:
        return False, f"Connection timed out reaching {normalized_host}"
    except ValueError as exc:
        message = str(exc)
        if "invalid" in message.lower() or "password" in message.lower() or "authentication" in message.lower():
            return False, "Authentication failed — invalid username or password"
        return False, message
    except Exception as exc:
        return False, str(exc)


async def get_system_info(host: str, username: str, password: str) -> dict[str, Any]:
    async with nextgen_session(host, username, password) as client:
        return await client.get_system_info()


async def list_applications(host: str, username: str, password: str) -> list[dict[str, Any]]:
    async with nextgen_session(host, username, password) as client:
        applications = await client.get_applications()
        return [_normalize_application(item) for item in applications]


async def list_virtual_servers(host: str, username: str, password: str) -> dict[str, Any]:
    async with nextgen_session(host, username, password) as client:
        return await client.list_virtual_servers()


async def create_application(
    host: str,
    username: str,
    password: str,
    name: str,
    virtual_ip: str,
    port: int,
    protocol: str,
    servers: list[str],
    *,
    servers_port: int | None = None,
    servers_protocol: str | None = None,
) -> dict[str, Any]:
    async with nextgen_session(host, username, password) as client:
        return await client.create_application(
            name,
            virtual_ip,
            port,
            protocol,
            servers,
            servers_port=servers_port,
            servers_protocol=servers_protocol,
        )


async def list_virtual_ips(host: str, username: str, password: str) -> list[dict[str, Any]]:
    async with nextgen_session(host, username, password) as client:
        return await client.list_virtual_ips()


async def list_ip_addresses(host: str, username: str, password: str) -> dict[str, Any]:
    async with nextgen_session(host, username, password) as client:
        return await client.list_ip_addresses()


async def nextgen_get(host: str, username: str, password: str, path: str) -> dict[str, Any]:
    async with nextgen_session(host, username, password) as client:
        return await client.get_resource(path)


async def nextgen_request(
    host: str,
    username: str,
    password: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generic Next-Gen API call: GET/POST/PUT/DELETE against any resource path."""
    verb = (method or "GET").strip().upper()
    cleaned_path = path.strip().lstrip("/")
    if not cleaned_path:
        raise ValueError("path is required")

    async with nextgen_session(host, username, password) as client:
        data = await client.request(verb, cleaned_path, body)

    return {
        "success": True,
        "transport": "Next-Gen API",
        "method": verb,
        "path": cleaned_path,
        "operation": f"{verb} {NEXTGEN_API_PREFIX}/{cleaned_path}",
        "response": data,
    }


async def ssh_run_command(
    host: str,
    username: str,
    password: str,
    command: str,
) -> dict[str, Any]:
    from app.services.config_service import get_runtime_config
    from app.services.ssh_service import run_ssh_command

    config = get_runtime_config()
    if not config.ssh_fallback_enabled:
        raise ValueError("SSH fallback is disabled in MCP configuration")

    return await run_ssh_command(
        host,
        username,
        password,
        command,
        port=config.ssh_port,
        timeout=float(config.ssh_timeout_seconds),
    )


async def run_cli_command(
    host: str,
    username: str,
    password: str,
    command: str,
) -> dict[str, Any]:
    """Run any NetScaler classic CLI command (read or write) over SSH."""
    from app.services.config_service import get_runtime_config
    from app.services.ssh_service import run_ssh_command

    config = get_runtime_config()
    if not config.ssh_fallback_enabled:
        raise ValueError("SSH access is disabled in MCP configuration")

    return await run_ssh_command(
        host,
        username,
        password,
        command,
        port=config.ssh_port,
        timeout=float(config.ssh_timeout_seconds),
        allow_writes=True,
    )


async def run_cli_commands(
    host: str,
    username: str,
    password: str,
    commands: list[str],
    *,
    stop_on_error: bool = True,
) -> dict[str, Any]:
    """Run a sequence of classic CLI commands over SSH, stopping on first failure by default."""
    cleaned = [cmd.strip() for cmd in commands if cmd and cmd.strip()]
    if not cleaned:
        raise ValueError("At least one command is required")

    results: list[dict[str, Any]] = []
    for command in cleaned:
        result = await run_cli_command(host, username, password, command)
        results.append(result)
        if stop_on_error and not result.get("success"):
            break

    return {
        "success": all(item.get("success") for item in results),
        "transport": "SSH",
        "commandCount": len(cleaned),
        "executedCount": len(results),
        "results": results,
    }


ALLOWED_NSIP_TYPES = frozenset({"NSIP", "SNIP", "VIP", "MIP", "GSLBSITEIP"})


def _validate_ip_address(ip_address: str) -> str:
    cleaned = ip_address.strip()
    if not _looks_like_ip(cleaned):
        raise ValueError(f"Invalid IP address: {ip_address}")
    return cleaned


def _normalize_nsip_type(ip_type: str) -> str:
    normalized = ip_type.strip().upper().replace(" ", "")
    if normalized == "GSLBSITEIP":
        return "GSLBsiteIP"
    if normalized not in ALLOWED_NSIP_TYPES and normalized != "GSLBSITEIP":
        raise ValueError(f"ip_type must be one of: NSIP, SNIP, VIP, MIP, GSLBsiteIP (got {ip_type})")
    return "GSLBsiteIP" if normalized == "GSLBSITEIP" else normalized


async def _nitro_post_nsconfig_save(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    response = await client.post(
        f"{base_url}/config/nsconfig?action=save",
        json={"nsconfig": {}},
        headers={**headers, "Content-Type": "application/json"},
    )
    payload = response.json()
    if response.status_code >= 400 or payload.get("errorcode", 0) != 0:
        message = payload.get("message") or _extract_error_message(response)
        raise ValueError(message or f"save ns config failed with HTTP {response.status_code}")
    return payload


async def add_ip_address(
    host: str,
    username: str,
    password: str,
    ip_address: str,
    ip_type: str = "VIP",
    netmask: str = "255.255.255.0",
    *,
    save_config: bool = True,
) -> dict[str, Any]:
    """Add a classic NSIP/SNIP/VIP via NITRO (add ns ip equivalent)."""
    from app.services.config_service import get_runtime_config

    config = get_runtime_config()
    target = normalize_host(host)
    cleaned_ip = _validate_ip_address(ip_address)
    cleaned_type = _normalize_nsip_type(ip_type)
    cleaned_mask = netmask.strip() or "255.255.255.0"

    base_url = f"https://{target}/nitro/v1"
    headers = {
        "Accept": "application/json",
        "X-NITRO-USER": username,
        "X-NITRO-PASS": password,
    }
    body = {
        "nsip": {
            "ipaddress": cleaned_ip,
            "netmask": cleaned_mask,
            "type": cleaned_type,
        }
    }

    async with httpx.AsyncClient(verify=config.verify_ssl, timeout=float(config.nitro_timeout_seconds)) as client:
        response = await client.post(
            f"{base_url}/config/nsip",
            json=body,
            headers={**headers, "Content-Type": "application/json"},
        )
        payload = response.json()
        if response.status_code >= 400 or payload.get("errorcode", 0) != 0:
            message = payload.get("message") or _extract_error_message(response)
            raise ValueError(message or f"add ns ip failed with HTTP {response.status_code}")

        result: dict[str, Any] = {
            "success": True,
            "transport": "NITRO",
            "operation": "add ns ip",
            "ipAddress": cleaned_ip,
            "type": cleaned_type,
            "netmask": cleaned_mask,
            "host": target,
            "classicCliEquivalent": f"add ns ip {cleaned_ip} {cleaned_mask} -type {cleaned_type}",
            "configSaved": False,
        }

        if save_config:
            try:
                await _nitro_post_nsconfig_save(client, base_url, headers)
                result["configSaved"] = True
            except ValueError as exc:
                result["configSaved"] = False
                result["saveWarning"] = str(exc)

        return result


# Backward-compatible alias used by existing REST routes.
async def list_lb_vservers(host: str, username: str, password: str) -> list[dict[str, Any]]:
    return await list_applications(host, username, password)


def format_tool_result(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)
