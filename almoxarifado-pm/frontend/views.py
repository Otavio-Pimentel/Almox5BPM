from django.shortcuts import render

def index(request): return render(request, 'index.html')
def login(request): return render(request, 'login.html')
def cautelas(request): return render(request, 'cautelas.html')
def estoque(request): return render(request, 'estoque.html')
def efetivo(request): return render(request, 'efetivo.html')