# criar_apps.py
import os

# Estrutura de apps
APPS = {
    'apps': {
        '__init__.py': '# Apps do projeto',
        'core': {
            '__init__.py': '# App de infraestrutura',
            'apps.py': '''from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Infraestrutura'
''',
        },
        'efetivo': {
            '__init__.py': '# App de efetivo',
            'apps.py': '''from django.apps import AppConfig

class EfetivoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.efetivo'
    verbose_name = 'Efetivo'
''',
        },
        'estoque': {
            '__init__.py': '# App de estoque',
            'apps.py': '''from django.apps import AppConfig

class EstoqueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.estoque'
    verbose_name = 'Estoque'
''',
        },
        'cautelas': {
            '__init__.py': '# App de cautelas',
            'apps.py': '''from django.apps import AppConfig

class CautelasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cautelas'
    verbose_name = 'Cautelas'
''',
        },
    }
}

def criar_estrutura(base_path, estrutura):
    """Cria a estrutura de pastas e arquivos"""
    for nome, conteudo in estrutura.items():
        caminho = os.path.join(base_path, nome)
        
        if isinstance(conteudo, dict):
            # É uma pasta
            os.makedirs(caminho, exist_ok=True)
            print(f'✅ Pasta criada: {caminho}')
            criar_estrutura(caminho, conteudo)
        else:
            # É um arquivo
            with open(caminho, 'w') as f:
                f.write(conteudo)
            print(f'✅ Arquivo criado: {caminho}')

# Executa
criar_estrutura('.', APPS)
print('\n✅ Estrutura de apps criada com sucesso!')