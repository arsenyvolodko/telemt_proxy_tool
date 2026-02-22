import logging
import re
from pathlib import Path

from server.api.dto.client import ClientsProxyRequest, RemoveClientsRequest

logger = logging.getLogger(__name__)

SECTION_HEADER = "[access.users]"
TOML_PATH_ENV = "TELEMT_TOML_PATH"


def _telemt_toml_path() -> Path:
    path = "./telemt.toml"
    return Path(path).resolve()


def _parse_access_users(content: str) -> dict[str, str]:
    """Из текста telemt.toml извлекает секцию [access.users] как словарь key -> value."""
    lines = content.splitlines()
    users = {}
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == SECTION_HEADER:
            in_section = True
            continue
        if in_section:
            if stripped.startswith("["):
                break
            match = re.match(r'^(\S+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*$', stripped)
            if match:
                raw = match.group(2).replace("\\\\", "\\").replace('\\"', '"')
                users[match.group(1)] = raw
    return users


def _format_access_users(users: dict[str, str]) -> str:
    """Форматирует словарь в блок TOML [access.users]."""
    lines = [SECTION_HEADER, ""]
    for key, value in sorted(users.items()):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key} = "{escaped}"')
    return "\n".join(lines) + "\n"


def _replace_section_in_content(content: str, new_section_block: str) -> str:
    """Подставляет новый блок [access.users] в содержимое файла. Если секции нет — добавляет перед [[upstreams]] или в конец."""
    lines = content.splitlines(keepends=True)
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = i
            continue
        if start is not None and end is None:
            if line.strip().startswith("["):
                end = i
                break
    if end is None and start is not None:
        end = len(lines)

    if start is not None and end is not None:
        before = "".join(lines[:start])
        after = "".join(lines[end:])
        return before + new_section_block + after

    insert_marker = "[[upstreams]]"
    for i, line in enumerate(lines):
        if insert_marker in line:
            return "".join(lines[:i]) + new_section_block + "".join(lines[i:])
    return content.rstrip() + "\n\n" + new_section_block


def _read_users(toml_path: Path) -> dict[str, str]:
    if not toml_path.exists():
        return {}
    return _parse_access_users(toml_path.read_text(encoding="utf-8"))


def _write_users(toml_path: Path, users: dict[str, str]) -> None:
    content = toml_path.read_text(encoding="utf-8")
    block = _format_access_users(users)
    new_content = _replace_section_in_content(content, block)
    toml_path.write_text(new_content, encoding="utf-8")


class TelemtTool:

    @classmethod
    def add_proxy_clients(cls, request: ClientsProxyRequest) -> bool:
        toml_path = _telemt_toml_path()
        if not toml_path.exists():
            logger.error("telemt.toml not found: %s", toml_path)
            return False
        try:
            users = _read_users(toml_path)
            for c in request.clients:
                users[c.telegram_id] = c.secret
            _write_users(toml_path, users)
            return True
        except Exception as e:
            logger.exception("Failed to add proxy clients: %s", e)
            return False

    @classmethod
    def remove_proxy_clients(cls, request: RemoveClientsRequest) -> bool:
        toml_path = _telemt_toml_path()
        if not toml_path.exists():
            logger.error("telemt.toml not found: %s", toml_path)
            return False
        try:
            users = _read_users(toml_path)
            for c in request.clients:
                users.pop(c.telegram_id, None)
            _write_users(toml_path, users)
            return True
        except Exception as e:
            logger.exception("Failed to remove proxy clients: %s", e)
            return False
