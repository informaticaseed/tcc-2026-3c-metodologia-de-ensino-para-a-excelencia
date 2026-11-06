"""
Constantes acadêmicas compartilhadas pelo sistema.

Este é o único lugar que deve ser alterado quando o conjunto de séries ou
de turmas atendidas pelo sistema mudar. As telas e as validações do backend
consomem estas definições.
"""

# Cada série possui o valor persistido no banco e o rótulo exibido na tela.
SERIES_ENSINO_MEDIO = (
    {"valor": "1º ano EM", "rotulo": "1º ano do Ensino Médio"},
    {"valor": "2º ano EM", "rotulo": "2º ano do Ensino Médio"},
    {"valor": "3º ano EM", "rotulo": "3º ano do Ensino Médio"},
)

# Atalho para validações e para o gerador de dados.
SERIES_ENSINO_MEDIO_VALORES = tuple(
    serie["valor"] for serie in SERIES_ENSINO_MEDIO
)

TURMAS = ("A", "B", "C", "D", "E", "F")


def serie_valida(serie):
    """Indica se a série informada é atendida pelo sistema."""
    return serie in SERIES_ENSINO_MEDIO_VALORES


def turma_valida(turma):
    """Indica se a turma informada está cadastrada no sistema."""
    return turma in TURMAS
