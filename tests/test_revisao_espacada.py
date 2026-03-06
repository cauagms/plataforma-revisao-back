from datetime import datetime, date, timedelta, timezone
from types import SimpleNamespace

import app.models.revisao  # noqa: F401
from app.models.user import RoleEnum
from app.services import estudar_hoje as estudar_hoje_service
from app.services import revisao as revisao_service
from app.services import topico as topico_service
from app.services.estudar_hoje import (
    INTERVALOS_REVISAO,
    calcular_primeira_revisao_em,
    calcular_proxima_revisao,
    classificar_status_revisao,
)


class TestIntervalosRevisao:
    def test_sequencia_correta(self):
        assert INTERVALOS_REVISAO == [1, 3, 7, 15, 30]

    def test_total_de_5_intervalos(self):
        assert len(INTERVALOS_REVISAO) == 5


class TestCalcularProximaRevisao:
    def test_zero_revisoes_usa_criado_em(self):
        criado = datetime(2026, 3, 1, 10, 0, 0)
        resultado = calcular_proxima_revisao(0, None, criado)
        assert resultado == date(2026, 3, 2)  # +1 dia

    def test_zero_revisoes_sem_criado_em_retorna_none(self):
        resultado = calcular_proxima_revisao(0, None, None)
        assert resultado is None

    def test_1_revisao_proxima_em_3_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(1, ultima)
        assert resultado == date(2026, 3, 8)  # +3 dias

    def test_2_revisoes_proxima_em_7_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(2, ultima)
        assert resultado == date(2026, 3, 12)  # +7 dias

    def test_3_revisoes_proxima_em_15_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(3, ultima)
        assert resultado == date(2026, 3, 20)  # +15 dias

    def test_4_revisoes_proxima_em_30_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(4, ultima)
        assert resultado == date(2026, 4, 4)  # +30 dias

    def test_5_revisoes_mantem_30_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(5, ultima)
        assert resultado == date(2026, 4, 4)  # +30 dias

    def test_10_revisoes_mantem_30_dias(self):
        ultima = datetime(2026, 3, 5, 14, 0, 0)
        resultado = calcular_proxima_revisao(10, ultima)
        assert resultado == date(2026, 4, 4)  # +30 dias

    def test_revisao_com_ultima_none_retorna_none(self):
        resultado = calcular_proxima_revisao(2, None)
        assert resultado is None


class TestPrimeiraRevisao:
    def test_primeira_revisao_vence_em_24h_exatas(self):
        criado = datetime(2026, 3, 5, 5, 56, 42)
        resultado = calcular_primeira_revisao_em(criado)
        assert resultado == datetime(2026, 3, 6, 1, 56, 42, tzinfo=estudar_hoje_service.MANAUS_TZ)

    def test_primeira_revisao_vira_atrasada_ao_bater_24h(self):
        criado = datetime(2026, 3, 5, 5, 56, 42)
        agora = datetime(2026, 3, 6, 1, 56, 42, tzinfo=estudar_hoje_service.MANAUS_TZ)
        status, proxima = classificar_status_revisao(0, None, criado, agora)
        assert status == estudar_hoje_service.StatusRevisao.atrasado
        assert proxima == date(2026, 3, 6)

    def test_primeira_revisao_ainda_nao_entra_antes_das_24h(self):
        criado = datetime(2026, 3, 5, 5, 56, 42)
        agora = datetime(2026, 3, 6, 1, 56, 41, tzinfo=estudar_hoje_service.MANAUS_TZ)
        status, proxima = classificar_status_revisao(0, None, criado, agora)
        assert status == estudar_hoje_service.StatusRevisao.primeira_revisao
        assert proxima == date(2026, 3, 6)


class TestEstudarHojeManaus:
    def test_topico_novo_entra_imediatamente_como_primeira_revisao(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 5, 2, 0, 0, tzinfo=estudar_hoje_service.MANAUS_TZ)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        class FakeQuery:
            def __init__(self, topicos):
                self._topicos = topicos

            def join(self, *_args, **_kwargs):
                return self

            def options(self, *_args, **_kwargs):
                return self

            def filter(self, *_args, **_kwargs):
                return self

            def all(self):
                return self._topicos

        class FakeDB:
            def __init__(self, topicos):
                self._topicos = topicos

            def query(self, *_args, **_kwargs):
                return FakeQuery(self._topicos)

        monkeypatch.setattr(estudar_hoje_service, "datetime", FixedDateTime)

        disciplina = SimpleNamespace(id=10, nome="Matematica", cor="#112233")
        topico = SimpleNamespace(
            id=20,
            titulo="Metodologia Agil",
            disciplina_id=disciplina.id,
            disciplina=disciplina,
            revisoes=[],
            criado_em=datetime(2026, 3, 5, 5, 56, 42),
        )
        usuario = SimpleNamespace(id=1, role=RoleEnum.professor)

        resultado = estudar_hoje_service.obter_estudar_hoje(FakeDB([topico]), usuario)

        assert resultado["resumo"]["topicos_para_hoje"] == 1
        assert resultado["resumo"]["atrasados"] == 0
        assert resultado["topicos"][0]["status"] == estudar_hoje_service.StatusRevisao.primeira_revisao

    def test_topico_criado_0156_entra_no_dia_de_manaus(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 6, 12, 0, 0, tzinfo=estudar_hoje_service.MANAUS_TZ)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        class FakeQuery:
            def __init__(self, topicos):
                self._topicos = topicos

            def join(self, *_args, **_kwargs):
                return self

            def options(self, *_args, **_kwargs):
                return self

            def filter(self, *_args, **_kwargs):
                return self

            def all(self):
                return self._topicos

        class FakeDB:
            def __init__(self, topicos):
                self._topicos = topicos

            def query(self, *_args, **_kwargs):
                return FakeQuery(self._topicos)

        monkeypatch.setattr(estudar_hoje_service, "datetime", FixedDateTime)

        disciplina = SimpleNamespace(id=10, nome="Matematica", cor="#112233")
        topico = SimpleNamespace(
            id=20,
            titulo="Logaritmos",
            disciplina_id=disciplina.id,
            disciplina=disciplina,
            revisoes=[],
            # Naive: tratado como UTC. 05:56 UTC = 01:56 do mesmo dia em Manaus.
            criado_em=datetime(2026, 3, 5, 5, 56, 0),
        )
        usuario = SimpleNamespace(id=1, role=RoleEnum.professor)

        resultado = estudar_hoje_service.obter_estudar_hoje(FakeDB([topico]), usuario)

        assert resultado["resumo"]["topicos_para_hoje"] == 1
        assert resultado["topicos"][0]["topico_id"] == topico.id

    def test_topico_sem_revisoes_so_fica_atrasado_apos_24h_exatas(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 6, 1, 56, 42, tzinfo=estudar_hoje_service.MANAUS_TZ)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        class FakeQuery:
            def __init__(self, topicos):
                self._topicos = topicos

            def join(self, *_args, **_kwargs):
                return self

            def options(self, *_args, **_kwargs):
                return self

            def filter(self, *_args, **_kwargs):
                return self

            def all(self):
                return self._topicos

        class FakeDB:
            def __init__(self, topicos):
                self._topicos = topicos

            def query(self, *_args, **_kwargs):
                return FakeQuery(self._topicos)

        monkeypatch.setattr(estudar_hoje_service, "datetime", FixedDateTime)

        disciplina = SimpleNamespace(id=10, nome="Matematica", cor="#112233")
        topico = SimpleNamespace(
            id=20,
            titulo="Metodologia Agil",
            disciplina_id=disciplina.id,
            disciplina=disciplina,
            revisoes=[],
            criado_em=datetime(2026, 3, 5, 5, 56, 42),
        )
        usuario = SimpleNamespace(id=1, role=RoleEnum.professor)

        resultado = estudar_hoje_service.obter_estudar_hoje(FakeDB([topico]), usuario)

        assert resultado["resumo"]["topicos_para_hoje"] == 1
        assert resultado["resumo"]["atrasados"] == 1
        assert resultado["topicos"][0]["status"] == estudar_hoje_service.StatusRevisao.atrasado


class TestStatusTopico:
    def test_topico_sem_revisoes_permanece_pendente_antes_das_24h(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 5, 2, 0, 0, tzinfo=estudar_hoje_service.MANAUS_TZ)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        monkeypatch.setattr(estudar_hoje_service, "datetime", FixedDateTime)

        topico = SimpleNamespace(
            id=20,
            titulo="Metodologia Agil",
            conteudo=None,
            disciplina_id=10,
            criado_em=datetime(2026, 3, 5, 5, 56, 42),
            atualizado_em=datetime(2026, 3, 5, 5, 56, 42),
            revisoes=[],
        )

        resultado = topico_service._enriquecer_topico(topico)

        assert resultado["status"] == "Pendente"

    def test_topico_sem_revisoes_fica_atrasado_apos_24h(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 6, 1, 56, 42, tzinfo=estudar_hoje_service.MANAUS_TZ)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        monkeypatch.setattr(estudar_hoje_service, "datetime", FixedDateTime)

        topico = SimpleNamespace(
            id=20,
            titulo="Metodologia Agil",
            conteudo=None,
            disciplina_id=10,
            criado_em=datetime(2026, 3, 5, 5, 56, 42),
            atualizado_em=datetime(2026, 3, 5, 5, 56, 42),
            revisoes=[],
        )

        resultado = topico_service._enriquecer_topico(topico)

        assert resultado["status"] == "Atrasado"


class TestPersistenciaTimestamps:
    def test_criar_revisao_define_criado_em_em_utc(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 6, 15, 0, 0, tzinfo=timezone.utc)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        class FakeDB:
            def __init__(self):
                self.obj = None

            def query(self, *_args, **_kwargs):
                class FakeQuery:
                    def filter(self, *_args, **_kwargs):
                        return self

                    def first(self):
                        return SimpleNamespace(id=1, user_id=1)

                return FakeQuery()

            def add(self, obj):
                self.obj = obj

            def commit(self):
                return None

            def refresh(self, _obj):
                return None

        monkeypatch.setattr(revisao_service, "datetime", FixedDateTime)
        monkeypatch.setattr(revisao_service, "_obter_topico_autorizado", lambda *args, **kwargs: SimpleNamespace(id=1))

        db = FakeDB()
        usuario = SimpleNamespace(id=1, role=RoleEnum.aluno)
        dados = SimpleNamespace(reflexao="ok")

        revisao = revisao_service.criar_revisao(db, 1, 1, dados, usuario)

        assert revisao.criado_em == datetime(2026, 3, 6, 15, 0, 0, tzinfo=timezone.utc)

    def test_criar_topico_define_timestamps_em_utc(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                fixo = datetime(2026, 3, 6, 15, 0, 0, tzinfo=timezone.utc)
                if tz is None:
                    return fixo.replace(tzinfo=None)
                return fixo.astimezone(tz)

        class FakeDB:
            def __init__(self):
                self.obj = None

            def add(self, obj):
                self.obj = obj

            def commit(self):
                return None

            def refresh(self, _obj):
                return None

        monkeypatch.setattr(topico_service, "datetime", FixedDateTime)
        monkeypatch.setattr(
            topico_service,
            "_obter_disciplina_autorizada",
            lambda *args, **kwargs: SimpleNamespace(id=10),
        )

        db = FakeDB()
        usuario = SimpleNamespace(id=1, role=RoleEnum.aluno)
        dados = SimpleNamespace(titulo="Tema", conteudo="Conteudo")

        topico = topico_service.criar_topico(db, 10, dados, usuario)

        esperado = datetime(2026, 3, 6, 15, 0, 0, tzinfo=timezone.utc)
        assert topico.criado_em == esperado
        assert topico.atualizado_em == esperado
