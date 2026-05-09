# apps/efetivo/serializers.py
#
# Serializers do app efetivo.
#
# Contrato de payload (compatibilidade com frontend):
#   Os nomes de campo, tipos e nulabilidade são idênticos ao
#   PolicialBase / PolicialResponse do schemas.py (Pydantic).
#
# Arquitetura de dois serializers:
#   PolicialBriefSerializer → leitura aninhada dentro de CautelaSerializer
#   PolicialSerializer      → CRUD completo no endpoint /policiais/
#
from rest_framework import serializers

from .models import Policial


# ─────────────────────────────────────────────────────────────
# SERIALIZER RESUMIDO
# Usado como campo aninhado em CautelaSerializer (read-only).
# Expõe apenas os campos usados pelo frontend no contexto de cautela.
# ─────────────────────────────────────────────────────────────
class PolicialBriefSerializer(serializers.ModelSerializer):
    """
    Representação compacta de Policial.

    Campos mínimos que o frontend consome em:
        c.policial?.posto_graduacao
        c.policial?.nome_guerra
        c.policial?.matricula
    """

    class Meta:
        model  = Policial
        fields = [
            'id',
            'matricula',
            'nome_guerra',
            'nome_completo',
            'posto_graduacao',
            'companhia_pelotao',
            'status',
            'criado_em',
        ]


# ─────────────────────────────────────────────────────────────
# SERIALIZER COMPLETO
# Usado no endpoint /policiais/ (list, create, retrieve, update).
# ─────────────────────────────────────────────────────────────
class PolicialSerializer(serializers.ModelSerializer):
    """
    Serializer principal de Policial.

    Compatibilidade de payload (PolicialResponse do FastAPI):
        id              int         read-only
        matricula       str         required, max 20
        nome_guerra     str         required, min 2
        nome_completo   str|null    opcional
        posto_graduacao str         required (choices)
        companhia_pelotao str|null  opcional
        status          str         default 'Ativo'
        criado_em       datetime    read-only

    Validações preservadas do Pydantic:
        - matricula: min_length=1, strip
        - nome_guerra: min_length=2, normalizado para maiúsculas
        - status: apenas valores do enum StatusPolicial
    """

    class Meta:
        model  = Policial
        fields = [
            'id',
            'matricula',
            'nome_guerra',
            'nome_completo',
            'posto_graduacao',
            'companhia_pelotao',
            'status',
            'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']
        extra_kwargs = {
            'matricula': {
                'max_length': 20,
            },
            'nome_guerra': {
                'min_length': 2,
                'max_length': 100,
            },
            'nome_completo': {
                'allow_null': True,
                'required': False,
            },
            'companhia_pelotao': {
                'allow_null': True,
                'allow_blank': True,
                'required': False,
            },
            'status': {
                'default': Policial.Status.ATIVO,
            },
        }

    def validate_matricula(self, value: str) -> str:
        """Normaliza e verifica unicidade de matrícula."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Matrícula não pode ser vazia.')

        # Em update (PATCH/PUT), exclui a própria instância da verificação
        qs = Policial.objects.filter(matricula=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"Matrícula '{value}' já cadastrada."
            )
        return value

    def validate_nome_guerra(self, value: str) -> str:
        """Normaliza nome de guerra para maiúsculas (padrão PM)."""
        value = value.strip().upper()
        if len(value) < 2:
            raise serializers.ValidationError('Nome de guerra muito curto.')
        return value

    def validate_status(self, value: str) -> str:
        """Garante que o status seja um dos valores permitidos."""
        valores_validos = [choice[0] for choice in Policial.Status.choices]
        if value not in valores_validos:
            raise serializers.ValidationError(
                f"Status inválido. Valores aceitos: {', '.join(valores_validos)}"
            )
        return value

    def validate_posto_graduacao(self, value: str) -> str:
        """Garante que o posto seja um dos valores permitidos."""
        valores_validos = [choice[0] for choice in Policial.PostoGraduacao.choices]
        if value not in valores_validos:
            raise serializers.ValidationError(
                f"Posto/graduação inválido. Valores aceitos: {', '.join(valores_validos)}"
            )
        return value
