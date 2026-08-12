from app.models.base import Base
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.estudante import Estudante
from app.models.estudante_universidade import EstudanteUniversidade, StatusJornada
from app.models.noticia import Noticia
from app.models.requisito import RequisitoCurso
from app.models.universidade import Curso, FonteDado, GrauCurso, Universidade

__all__ = [
    "Base",
    "CategoriaDocumento",
    "Curso",
    "Documento",
    "Estudante",
    "EstudanteUniversidade",
    "FonteDado",
    "GrauCurso",
    "Noticia",
    "RequisitoCurso",
    "StatusDocumento",
    "StatusJornada",
    "Universidade",
]
