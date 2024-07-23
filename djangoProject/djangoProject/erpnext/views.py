import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import json
from django.http import JsonResponse
import random
import string

@api_view(['GET'])
def erpnext(request):
    # URL base do seu ERPNext
    base_url = "http://192.168.60.13:8080"

    # Endpoint para buscar a lista de itens
    endpoint = "/api/resource/Item"

    # As suas credenciais de API
    api_key = "528eff3406d6c19"
    api_secret = "197ffe63e0ced95"

    # Headers de autenticação
    headers = {
        "Authorization": f"token {api_key}:{api_secret}"
    }

    # Carregar o último código atualizado
    try:
        with open('last_custom_code.txt', 'r') as file:
            last_code = int(file.read().strip())
    except FileNotFoundError:
        last_code = 0

    # Variável para manter o código sequencial
    code = last_code + 1

    # Contador para limitar o número de atualizações por batch
    batch_size = 3000
    updates_done = 0

    try:
        while True:
            # Parâmetros da consulta
            params = {
                "fields": '["name", "custom_codigo"]',  # Buscar apenas os campos necessários
                "limit_page_length": batch_size,  # Limitar o número de resultados a 100 por vez
                "filters": '{"custom_codigo": ["=", ""]} ',  # Filtrar itens sem custom_codigo
                "order_by": "creation asc"  # Ordenar por data de criação
            }

            # Fazendo a requisição GET para obter a lista de itens
            response = requests.get(base_url + endpoint, headers=headers, params=params, timeout=120)
            response.raise_for_status()

            items = response.json().get('data', [])

            if not items:
                break  # Sai do loop se não houver mais itens para atualizar

            # Conjunto para armazenar todos os códigos existentes
            existing_codes = set()

            # Obter todos os códigos existentes antes de atualizar
            for item in items:
                existing_code = item.get('custom_codigo')
                if existing_code:
                    existing_codes.add(existing_code)

            # Para cada item, atualizar o campo custom_codigo com um novo código único
            for item in items:
                if updates_done >= batch_size:
                    break

                item_name = item.get('name')

                # Gerar um código de 6 dígitos único
                new_code = generate_unique_code(existing_codes)
                existing_codes.add(new_code)

                # Endpoint para atualização
                update_endpoint = f"{base_url}/api/resource/Item/{item_name}"
                update_data = {
                    "custom_codigo": new_code
                }

                try:
                    # Fazendo a requisição PUT para atualizar o item
                    update_response = requests.put(update_endpoint, headers=headers, json=update_data, timeout=600)
                    update_response.raise_for_status()

                    print(f"Código {new_code} atualizado para o item {item_name}")

                    # Persistir o código atualizado
                    with open('last_custom_code.txt', 'w') as file:
                        file.write(new_code)

                    # Incrementar o contador de atualizações realizadas
                    updates_done += 1

                except requests.RequestException as e:
                    print(f"Erro ao atualizar código para o item {item_name}: {e}")

        return Response({"message": f"{updates_done} itens atualizados com sucesso"}, status=status.HTTP_200_OK)

    except requests.RequestException as e:
        return Response({"error": f"Erro ao buscar a lista de itens: {e}"}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def update_customer_codes(request):
    # URL base do seu ERPNext
    base_url = "http://192.168.60.13:8080"

    # Endpoint para buscar a lista de clientes
    endpoint = "/api/resource/Customer"

    # As suas credenciais de API
    api_key = "528eff3406d6c19"
    api_secret = "197ffe63e0ced95"

    # Headers de autenticação
    headers = {
        "Authorization": f"token {api_key}:{api_secret}"
    }

    try:
        # Parâmetros da consulta para buscar todos os clientes
        params_all_customers = {
            "fields": '["name", "custom_codigo"]',
            "limit_page_length": 10000,  # Ajuste o limite conforme necessário para buscar todos os clientes
        }

        # Fazendo a requisição GET para obter todos os clientes
        response_all_customers = requests.get(base_url + endpoint, headers=headers, params=params_all_customers, timeout=120)
        response_all_customers.raise_for_status()

        all_customers = response_all_customers.json().get('data', [])

        # Conjunto para armazenar todos os códigos existentes
        existing_codes = set()

        # Obter todos os códigos existentes antes de atualizar
        for customer in all_customers:
            existing_code = customer.get('custom_codigo')
            if existing_code:
                existing_codes.add(existing_code)

        # Contador para limitar o número de atualizações
        update_limit = 2000
        updates_done = 0

        # Para cada cliente, atualizar o campo custom_codigo com um novo código único
        for customer in all_customers:
            if updates_done >= update_limit:
                break

            customer_name = customer.get('name')

            # Verificar se o cliente já possui um código
            if customer.get('custom_codigo'):
                continue  # Pular clientes que já têm código definido

            # Gerar um código de 6 dígitos único
            new_code = generate_unique_code(existing_codes)
            existing_codes.add(new_code)

            # Endpoint para atualização
            update_endpoint = f"{base_url}/api/resource/Customer/{customer_name}"
            update_data = {
                "custom_codigo": new_code
            }

            try:
                # Fazendo a requisição PUT para atualizar o cliente
                update_response = requests.put(update_endpoint, headers=headers, json=update_data, timeout=600)
                update_response.raise_for_status()

                print(f"Código {new_code} atribuído ao cliente {customer_name}")

                # Incrementar o contador de atualizações realizadas
                updates_done += 1

            except requests.RequestException as e:
                print(f"Erro ao atualizar código para o cliente {customer_name}: {e}")

        return Response({"message": f"{updates_done} clientes atualizados com sucesso"}, status=status.HTTP_200_OK)

    except requests.RequestException as e:
        return Response({"error": f"Erro ao buscar a lista de clientes: {e}"}, status=status.HTTP_400_BAD_REQUEST)


def generate_unique_code(existing_codes):
    # Função para gerar um código único de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))
    while code in existing_codes:
        code = ''.join(random.choices(string.digits, k=6))
    return code
