import json
import logging
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

USUARIOS_PATH = Path(__file__).parent.parent / "data" / "usuarios.json"


@dataclass
class UserProfile:
    user_id: str
    name: str = ""
    age: int | None = None
    interest: str = ""
    status: str = "activo"
    last_query: str = ""
    last_interaction: str = ""
    created_at: str = ""
    query_count: int = 0

    def to_context_string(self) -> str:
        parts = []
        if self.name:
            parts.append(f"Nombre: {self.name}")
        if self.age:
            parts.append(f"Edad: {self.age}")
        if self.interest:
            parts.append(f"Interés: {self.interest}")
        if self.status != "activo":
            parts.append(f"Estado: {self.status}")
        if self.query_count > 0:
            parts.append(f"Consultas previas: {self.query_count}")
        if not parts:
            return ""
        return "Perfil del usuario: " + " | ".join(parts)


class UserMemory:
    def __init__(self, filepath: Path = USUARIOS_PATH):
        self._filepath = filepath
        self._users: dict[str, UserProfile] = {}
        self._load()

    def _load(self) -> None:
        if self._filepath.exists():
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid, udata in data.items():
                    self._users[uid] = UserProfile(**udata)
                logger.info(f"Loaded {len(self._users)} user profiles")
            except Exception as e:
                logger.error(f"Failed to load user profiles: {e}")
        else:
            self._save()

    def _save(self) -> None:
        try:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            data = {uid: asdict(profile) for uid, profile in self._users.items()}
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user profiles: {e}")

    def get_user(self, user_id: str) -> UserProfile:
        if user_id not in self._users:
            self._users[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.now().isoformat(),
            )
        return self._users[user_id]

    def update_user(self, user_id: str, **kwargs) -> UserProfile:
        user = self.get_user(user_id)
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        user.last_interaction = datetime.now().isoformat()
        self._save()
        return user

    def increment_query_count(self, user_id: str) -> None:
        user = self.get_user(user_id)
        user.query_count += 1
        user.last_interaction = datetime.now().isoformat()
        self._save()

    def extract_user_info(self, message: str) -> dict:
        info: dict = {}

        name_patterns = [
            r"(?i)me\s*llamo\s+(\w+)",
            r"(?i)mi\s*nombre\s*es\s+(\w+)",
            r"(?i)soy\s+(\w+)",
            r"(?i)mi\s*nombre:\s*(\w+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                info["name"] = match.group(1).capitalize()
                break

        age_patterns = [
            r"(?i)tengo\s+(\d{1,2})\s*a[ñn]os",
            r"(?i)mi\s*edad\s*(?:es|:)\s*(\d{1,2})",
            r"(?i)edad:\s*(\d{1,2})",
            r"(\d{1,2})\s*a[ñn]os",
        ]
        for pattern in age_patterns:
            match = re.search(pattern, message)
            if match:
                age = int(match.group(1))
                if 5 <= age <= 100:
                    info["age"] = age
                break

        interest_patterns = [
            r"(?i)(?:quiero|deseo|me\s*gustaría|interesado\s*en|inscribir|inscribirme\s*en)\s*(?:.*?)(?:curso\s*de\s*)?(ingl[eé]s|franc[eé]s|portugu[eé]s)",
            r"(?i)(?:curso\s*de\s*)(ingl[eé]s|franc[eé]s|portugu[eé]s)",
            r"(?i)(ingl[eé]s|franc[eé]s|portugu[eé]s)",
        ]
        for pattern in interest_patterns:
            match = re.search(pattern, message)
            if match:
                interest = match.group(1).lower()
                interest = interest.replace("é", "e")
                info["interest"] = interest
                break

        return info

    def get_context_for_user(self, user_id: str) -> str:
        user = self.get_user(user_id)
        return user.to_context_string()

    def get_all_users(self) -> list[UserProfile]:
        return list(self._users.values())


user_memory = UserMemory()
