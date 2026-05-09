# apps/estoque/serializers.py
#
# Serializers do app estoque.
#
# Contrato de payload (compatibilidade com frontend):
#   Os nomes de campo, tipos e nulabilidade são idênticos ao
#   ItemBase / ItemResponse do schemas.py (Pydantic).
#
# Arquitetura de dois serializers:
#   ItemBriefSerializer → leitura aninhada dentro de CautelaSerializer
#   ItemSerializer      → CRUD completo no endpoint /itens/
#
from rest_framework import serializers

from .models import Item


# ─────────────────────────────────────────────────────────────
# SERIALIZER RESUMIDO
# Usado como campo aninhado em CautelaSerializer (read-only).
# ─────────────────────────────────────────────────────────────
class ItemBriefSerializer(serializers.ModelSerializer):
    """
    Representação compacta de Item.

    Campos consumidos pelo frontend no contexto de cautela:
        c.item?.descricao
        c.item?.numero_serie
        c.item?.tipo_material
    """

    class Meta:
        model  = Item
        fields = [
            'id',
            'numero_serie',
            'tipo_material',
            'descricao',
            'quantidade_total',
            'quantidade_disponivel',
            'condicao',
            'localizacao',
            'observacoes',
            'criado_em',
            'atualizado_em',
        ]


# ─────────────────────────────────────────────────────────────
# SERIALIZER COMPLETO
# Usado no endpoint /itens/ (list, create, retrieve, update).
# ─────────────────────────────────────────────────────────────
class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer principal de Item.

    Compatibilidade de payload (ItemResponse do FastAPI):
        id                    int          read-only
        numero_serie          str|null     opcional (item seriado vs genérico)
        tipo_material         str          required (choices)
        descricao             str          required, min 2, max 200
        quantidade_total      int          default 1, >= 0
        quantidade_disponivel int          default 1, >= 0
        condicao              str          default 'Bom' (choices)
        localizacao           str|null     opcional
        observacoes           str|null     opcional
        criado_em             datetime     read-only
        atualizado_em         datetime     read-only

    Validações preservadas do Pydantic:
        - quantidade_disponivel <= quantidade_total
        - tipo_material deve ser um dos choices válidos
        - condicao deve ser um dos choices válidos
    """

    class Meta:
        model  = Item
        fields = [
            'id',
            'numero_serie',
            'tipo_material',
            'descricao',
            'quantidade_total',
            'quantidade_disponivel',
            'condicao',
            'localizacao',
            'observacoes',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'numero_serie': {
                'allow_null':  True,
                'allow_blank': True,
                'required':    False,
                'max_length':  100,
            },
            'descricao': {
                'min_length': 2,
                'max_length': 200,
            },
            'quantidade_total': {
                'default': 1,
                'min_value': 0,
            },
            'quantidade_disponivel': {
                'default': 1,
                'min_value': 0,
            },
            'condicao': {
                'default': Item.Condicao.BOM,
            },
            'localizacao': {
                'allow_null':  True,
                'allow_blank': True,
                'required':    False,
            },
            'observacoes': {
                'allow_null':  True,
                'allow_blank': True,
                'required':    False,
            },
        }

    def validate_numero_serie(self, value: str) -> str | None:
        """
        Normaliza número de série para maiúsculas.
        Verifica unicidade, excluindo a instância atual em updates.
        """
        if not value or not value.strip():
            return None  # Trata vazio como null (item genérico)

        value = value.strip().upper()

        qs = Item.objects.filter(numero_serie=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"Série '{value}' já cadastrada (ID {qs.first().pk})."
            )
        return value

    def validate_tipo_material(self, value: str) -> str:
        """Garante que o tipo de material seja um dos choices."""
        valores_validos = [choice[0] for choice in Item.TipoMaterial.choices]
        if value not in valores_validos:
            raise serializers.ValidationError(
                f"Tipo inválido. Valores aceitos: {', '.join(valores_validos)}"
            )
        return value

    def validate_condicao(self, value: str) -> str:
        """Garante que a condição seja um dos choices."""
        valores_validos = [choice[0] for choice in Item.Condicao.choices]
        if value not in valores_validos:
            raise serializers.ValidationError(
                f"Condição inválida. Valores aceitos: {', '.join(valores_validos)}"
            )
        return value

    def validate(self, data: dict) -> dict:
        """
        Validação cruzada: quantidade_disponivel <= quantidade_total.
        Preservada do Pydantic: 'Quantidade disponível > quantidade total'.
        """
        total     = data.get('quantidade_total',      getattr(self.instance, 'quantidade_total',      1))
        disponivel = data.get('quantidade_disponivel', getattr(self.instance, 'quantidade_disponivel', 1))

        if disponivel > total:
            raise serializers.ValidationError({
                'quantidade_disponivel': (
                    f'Quantidade disponível ({disponivel}) não pode ser maior '
                    f'que a quantidade total ({total}).'
                )
            })
        return data
