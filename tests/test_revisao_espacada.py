from datetime import datetime, date, timedelta
from types import SimpleNamespace

import app.models.revisao  # noqa: F401
from app.models.user import RoleEnum
from app.services import estudar_hoje as estudar_hoje_service
from app.services.estudar_hoje import INTERVALOS_REVISAO, calcular_proxima_revisao


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


class TestEstudarHojeManaus:
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
