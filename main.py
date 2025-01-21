import streamlit as st
import os
import math
from collections import defaultdict

class Rota:
    def __init__(self):
        self.paradas = [1]  # Começa sempre na parada 1
        self.colaboradores = []

def leitortodos(arquivo):
    with open(arquivo, 'r') as f:
        data = [line.split() for line in f.readlines()]

    p = int(data[0][0])
    x = int(data[0][2])
    y = int(data[0][4])
    e = x + y
    n = int(data[0][8])
    dist_max = float(data[0][6])

    coord_x_par = [float(data[i+1][1]) for i in range(p-1)]
    coord_y_par = [float(data[i+1][2]) for i in range(p-1)]

    coord_x_est = [float(data[i+p][1]) for i in range(e)]
    coord_y_est = [float(data[i+p][2]) for i in range(e)]
    vecDistMax_input = [float(data[i+p][3]) for i in range(e)]
    vecDurMax_input = [float(data[i+p][4]) for i in range(e)]

    return p, e, n, dist_max, coord_x_par, coord_y_par, coord_x_est, coord_y_est, vecDistMax_input, vecDurMax_input

def solve(arquivo):
    p, e, n, dist_max, coord_x_par, coord_y_par, coord_x_est, coord_y_est, vecDistMax_input, vecDurMax_input = leitortodos(arquivo)
    p -= 1

    if e == 0:
        st.error("Nenhum colaborador encontrado.")
        return [], coord_x_par, coord_y_par, {}

    capacidade_veiculo = n
    rotas = []
    colaboradores = list(range(1, e+1))
    paradas_visitadas = set()

    dist = [[0.0] * p for _ in range(e)]
    for i in range(e):
        for j in range(p):
            dist[i][j] = math.sqrt((coord_x_est[i] - coord_x_par[j])**2 + (coord_y_est[i] - coord_y_par[j])**2)

    colaboradores_alocados = defaultdict(list)

    while colaboradores:
        rota_atual = Rota()
        capacidade_atual = 0

        while capacidade_atual < capacidade_veiculo and colaboradores:
            melhor_parada = -1
            melhor_colaboradores = []

            for parada in range(p-1, 0, -1):
                if parada in paradas_visitadas:
                    continue
                
                proximos = []
                for i in colaboradores:
                    if dist[i-1][parada-1] <= vecDistMax_input[i-1]:
                        proximos.append(i)
                    elif dist[i-1][parada-1] <= 1.2 * vecDistMax_input[i-1]:
                        proximos.append(i)

                proximos_filtrados = []
                for i in proximos:
                    if (dist[i-1][parada-1] / 70 + dist[0][parada-1] / 70) <= vecDurMax_input[i-1]:
                        proximos_filtrados.append(i)
                    elif (dist[i-1][parada-1] / 70 + dist[0][parada-1] / 70) <= 1.2 * vecDurMax_input[i-1]:
                        proximos_filtrados.append(i)

                proximos = proximos_filtrados

                if proximos:
                    melhor_parada = parada
                    melhor_colaboradores = proximos
                    break

            if melhor_parada == -1:
                break

            if capacidade_atual + len(melhor_colaboradores) > capacidade_veiculo:
                break

            for i in melhor_colaboradores:
                if capacidade_atual < capacidade_veiculo:
                    rota_atual.colaboradores.append(i)
                    colaboradores.remove(i)
                    capacidade_atual += 1

                    if melhor_parada not in colaboradores_alocados:
                        colaboradores_alocados[melhor_parada] = []

                    colaboradores_alocados[melhor_parada].append(i)

            rota_atual.paradas.append(melhor_parada)
            paradas_visitadas.add(melhor_parada)

        rota_atual.paradas.append(1)

        if not rota_atual.colaboradores:
            break

        rotas.append(rota_atual)

    if colaboradores:
        for colaborador in colaboradores:
            paradas_validas = list(range(2, p+1))
            distancias = [dist[colaborador-1][parada-1] for parada in paradas_validas]
            parada_mais_proxima = paradas_validas[distancias.index(min(distancias))]

            colaboradores_alocados[parada_mais_proxima].append(colaborador)

    for i, rota in enumerate(rotas):
        paradas_invertidas = rota.paradas[::-1]  # Inverte as paradas para exibir em ordem inversa
        st.write(f"************** Rota do veículo {i+1}: {' '.join(map(str, paradas_invertidas))}")
        for parada in paradas_invertidas:
            if parada != 1:
                st.write(f"Parada {parada} contém os colaboradores: {' '.join(map(str, colaboradores_alocados[parada]))}")
        st.write()

    return rotas, coord_x_par, coord_y_par, colaboradores_alocados

def processar_arquivos(uploaded_files):
    # Certifique-se de que o diretório "uploads" exista
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    for arquivo in uploaded_files:
        arquivo_path = os.path.join(upload_dir, arquivo.name)
        with open(arquivo_path, "wb") as f:
            f.write(arquivo.getbuffer())
        
        rotas, coord_x_par, coord_y_par, colaboradores_alocados = solve(arquivo_path)
        st.success(f"Solução para {arquivo.name} processada!")

# Interface Streamlit
st.title("Sistema de Roteirização de Colaboradores")

st.header("Carregue seus arquivos de entrada")
uploaded_files = st.file_uploader("Escolha arquivos", type="txt", accept_multiple_files=True)

if uploaded_files:
    processar_arquivos(uploaded_files)
