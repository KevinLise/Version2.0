import pytest
import json
import tempfile
from pathlib import Path
from services.user_memory import UserMemory, UserProfile


@pytest.fixture
def temp_memory(tmp_path):
    filepath = tmp_path / "test_usuarios.json"
    return UserMemory(filepath=filepath)


class TestUserProfile:
    def test_default_profile(self):
        profile = UserProfile(user_id="123")
        assert profile.user_id == "123"
        assert profile.name == ""
        assert profile.age is None
        assert profile.interest == ""
        assert profile.status == "activo"
        assert profile.query_count == 0

    def test_context_string_empty(self):
        profile = UserProfile(user_id="123")
        assert profile.to_context_string() == ""

    def test_context_string_with_name(self):
        profile = UserProfile(user_id="123", name="Kevin")
        ctx = profile.to_context_string()
        assert "Kevin" in ctx
        assert "Nombre" in ctx

    def test_context_string_full(self):
        profile = UserProfile(user_id="123", name="Kevin", age=25, interest="ingles")
        ctx = profile.to_context_string()
        assert "Kevin" in ctx
        assert "25" in ctx
        assert "ingles" in ctx


class TestUserMemory:
    def test_get_new_user(self, temp_memory):
        user = temp_memory.get_user("user_001")
        assert user.user_id == "user_001"
        assert user.name == ""

    def test_update_user_name(self, temp_memory):
        temp_memory.update_user("user_001", name="Kevin")
        user = temp_memory.get_user("user_001")
        assert user.name == "Kevin"

    def test_update_user_age(self, temp_memory):
        temp_memory.update_user("user_001", age=25)
        user = temp_memory.get_user("user_001")
        assert user.age == 25

    def test_update_user_interest(self, temp_memory):
        temp_memory.update_user("user_001", interest="ingles")
        user = temp_memory.get_user("user_001")
        assert user.interest == "ingles"

    def test_persistence(self, tmp_path):
        filepath = tmp_path / "persist_test.json"
        mem1 = UserMemory(filepath=filepath)
        mem1.update_user("user_001", name="Kevin", age=25)

        mem2 = UserMemory(filepath=filepath)
        user = mem2.get_user("user_001")
        assert user.name == "Kevin"
        assert user.age == 25

    def test_increment_query_count(self, temp_memory):
        temp_memory.increment_query_count("user_001")
        temp_memory.increment_query_count("user_001")
        user = temp_memory.get_user("user_001")
        assert user.query_count == 2

    def test_get_context_for_user(self, temp_memory):
        temp_memory.update_user("user_001", name="Kevin", age=25)
        ctx = temp_memory.get_context_for_user("user_001")
        assert "Kevin" in ctx
        assert "25" in ctx

    def test_get_context_empty_user(self, temp_memory):
        ctx = temp_memory.get_context_for_user("new_user")
        assert ctx == ""


class TestExtractUserInfo:
    def test_me_llamo(self, temp_memory):
        info = temp_memory.extract_user_info("Hola, me llamo Kevin")
        assert info.get("name") == "Kevin"

    def test_mi_nombre_es(self, temp_memory):
        info = temp_memory.extract_user_info("Mi nombre es María")
        assert info.get("name") == "María"

    def test_soy(self, temp_memory):
        info = temp_memory.extract_user_info("Soy Carlos")
        assert info.get("name") == "Carlos"

    def test_tengo_edad(self, temp_memory):
        info = temp_memory.extract_user_info("Tengo 25 años")
        assert info.get("age") == 25

    def test_mi_edad_es(self, temp_memory):
        info = temp_memory.extract_user_info("Mi edad es 30")
        assert info.get("age") == 30

    def test_edad_format(self, temp_memory):
        info = temp_memory.extract_user_info("Edad: 22")
        assert info.get("age") == 22

    def test_invalid_age(self, temp_memory):
        info = temp_memory.extract_user_info("Tengo 3 años")
        assert info.get("age") is None

    def test_interest_ingles(self, temp_memory):
        info = temp_memory.extract_user_info("Quiero inscribirme en inglés")
        assert info.get("interest") == "ingles"

    def test_interest_frances(self, temp_memory):
        info = temp_memory.extract_user_info("Me interesa el curso de francés")
        assert info.get("interest") == "frances"

    def test_interest_portugues(self, temp_memory):
        info = temp_memory.extract_user_info("Curso de portugués")
        assert info.get("interest") == "portugues"

    def test_full_extraction(self, temp_memory):
        info = temp_memory.extract_user_info("Hola, me llamo Kevin, tengo 25 años y quiero inscribirme en inglés")
        assert info.get("name") == "Kevin"
        assert info.get("age") == 25
        assert info.get("interest") == "ingles"

    def test_no_info(self, temp_memory):
        info = temp_memory.extract_user_info("¿Cuánto cuesta el curso?")
        assert info == {}
