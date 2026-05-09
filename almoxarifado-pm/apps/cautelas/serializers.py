# apps/cautelas/serializers.py
#
# Serializers do app cautelas.
#
# Contrato de payload (compatibilidade com frontend):
#   Os nomes de campo, tipos e nulabilidade são idênticos ao
#   CautelaBase / CautelaResponse do schemas.py (Pydantic).
#
# Padrão de leitura vs escrita:
#
#   ESCRITA (POST /cautelas/):
#       Frontend envia:  policial_id (int), item_id (int)
#
#   LEITURA (GET /cautelas/, GET /cautelas/{id}):
#       Frontend recebe: policial_id (int)
#                        item_id     (int)
#                        policial    (object aninhado)
#                        item        (object aninhado)
#
#   Isso replica exatamente o comportamento do FastAPI com joinedload().
#
from rest_framework import serializers

from apps.efetivo.serializers import PolicialBriefSerializer
from apps.estoque.serializers import ItemBriefSerializer

from .models import Cautela


class CautelaSerializer(serializers.ModelSerializer):
    """
    Serializer completo de Cautela.

    Compatibilidade de payload (CautelaResponse do FastAPI):

        CAMPOS SIMPLES (leitura + escrita):
            id                      int         read-only
            policial_id             int         write (FK)
            item_id                 int         write (FK)
            quantidade              int         default 1, >= 1
            data_retirada           datetime    read-only (auto)
            data_devolucao_prevista datetime    opcional
            data_devolucao_real     datetime    opcional, read-only via devolver
            responsavel_entrega     str         required, min 2
            status                  str         read-only ('Ativa' na criação)
            observacoes             str|null    opcional
            criado_em               datetime    read-only

        CAMPOS ANINHADOS (somente leitura — para o frontend):
            policial                object      PolicialBriefSerializer
            item                    object      ItemBriefSerializer

    Nota sobre policial_id / item_id:
        O Django ORM gera automaticamente o campo policial_id (int)
        ao declarar ForeignKey(policial). O DRF expõe ambos:
            policial_id → inteiro (escrita e leitura)
            policial    → objeto aninhado (somente leitura)
        Isso preserva o contrato exato do CautelaResponse do Pydantic.
    """

    # Campos aninhados de leitura
    policial = PolicialBriefSerializer(read_only=True)
    item     = ItemBriefSerializer(read_only=True)

    class Meta:
        model  = Cautela
        fields = [
            'id',
            'policial_id',              # int FK — aceito na escrita
            'item_id',                  # int FK — aceito na escrita
            'policial',                 # obj aninhado — somente leitura
            'item',                     # obj aninhado — somente leitura
            'quantidade',
            'data_retirada',
            'data_devolucao_prevista',
            'data_devolucao_real',
            'responsavel_entrega',
            'status',
            'observacoes',
            'criado_em',
        ]
        read_only_fields = [
            'id',
            'policial',
            'item',
            'data_retirada',
            'data_devolucao_real',      # Atualizado apenas via /devolver
            'status',                   # Gerenciado pela view (máquina de estado)
            'criado_em',
        ]
        extra_kwargs = {
            'policial_id': {
                'required': True,
            },
            'item_id': {
                'required': True,
            },
            'quantidade': {
                'default':   1,
                'min_value': 1,
            },
            'data_devolucao_prevista': {
                'required':   False,
                'allow_null': True,
            },
            'responsavel_entrega': {
                'min_length': 2,
                'max_length': 100,
            },
            'observacoes': {
                'required':    False,
                'allow_null':  True,
                'allow_blank': True,
            },
        }

    def validate_responsavel_entrega(self, value: str) -> str:
        """Normaliza nome do responsável para maiúsculas."""
        return value.strip().upper()

    def validate_quantidade(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError('Quantidade mínima é 1.')
        return value


# ─────────────────────────────────────────────────────────────
# SERIALIZER DE DEVOLUÇÃO
# Usado exclusivamente no endpoint PUT /cautelas/{id}/devolver/
# Equivale ao CautelaDevolver do Pydantic.
# ─────────────────────────────────────────────────────────────
class CautelasDevolverSerializer(serializers.Serializer):
    """
    Payload aceito no endpoint de devolução.

    Compatibilidade (CautelaDevolver do FastAPI):
        data_devolucao_real    datetime|null    opcional
        observacoes            str|null         opcional
    """

    data_devolucao_real = serializers.DateTimeField(
        required=False,
        allow_null=True,
        default=None,
    )
    observacoes = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None,
    )
