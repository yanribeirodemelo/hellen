import streamlit as st
import os
import math
import matplotlib.pyplot as plt
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


def plot_rotas(rotas, coord_x_par, coord_y_par, coord_x_est, coord_y_est, colaboradores_alocados):
    plt.figure(figsize=(10, 8))

    # Plotando as paradas
    plt.scatter(coord_x_par, coord_y_par, c='blue', label='Paradas', s=100, marker='s')
    for i, (x, y) in enumerate(zip(coord_x_par, coord_y_par), start=1):
        plt.text(x, y, f'P{i}', fontsize=10, ha='right')

    # Plotando os colaboradores
    plt.scatter(coord_x_est, coord_y_est, c='green', label='Colaboradores', s=50, marker='o')
    for i, (x, y) in enumerate(zip(coord_x_est, coord_y_est), start=1):
        plt.text(x, y, f'C{i}', fontsize=8, ha='left')

    # Desenhando as rotas
    colors = ['red', 'purple', 'orange', 'brown', 'pink', 'cyan', 'magenta']
    for i, rota in enumerate(rotas):
        cor = colors[i % len(colors)]
        for parada in rota.paradas:
            if parada != 1:
                for colaborador in colaboradores_alocados[parada]:
                    # Linha do colaborador para a parada
                    plt.plot(
                        [coord_x_est[colaborador-1], coord_x_par[parada-1]],
                        [coord_y_est[colaborador-1], coord_y_par[parada-1]],
                        linestyle='--', color=cor, alpha=0.7
                    )

        # Linhas entre as paradas na rota
        for j in range(len(rota.paradas) - 1):
            origem = rota.paradas[j]
            destino = rota.paradas[j+1]
            plt.plot(
                [coord_x_par[origem-1], coord_x_par[destino-1]],
                [coord_y_par[origem-1], coord_y_par[destino-1]],
                linestyle='-', color=cor, linewidth=2, label=f'Rota {i+1}' if j == 0 else ""
            )

    plt.legend(loc='best')
    plt.title("Rotas Geradas")
    plt.xlabel("Coordenada X")
    plt.ylabel("Coordenada Y")
    plt.grid(True)

    # Salvar o gráfico como imagem temporária
    plt.savefig("rotas.png")
    st.pyplot(plt)  # Exibe o gráfico no Streamlit
    plt.close()

# Função `solve` com plotagem no Streamlit
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

    plot_rotas(rotas, coord_x_par, coord_y_par, coord_x_est, coord_y_est, colaboradores_alocados)
    return rotas, coord_x_par, coord_y_par, colaboradores_alocados


def processar_arquivos(uploaded_files):
    for arquivo in uploaded_files:
        arquivo_path = os.path.join("uploads", arquivo.name)
        with open(arquivo_path, "wb") as f:
            f.write(arquivo.getbuffer())
       
        rotas, coord_x_par, coord_y_par, colaboradores_alocados = solve(arquivo_path)
        st.success(f"Solução para {arquivo.name} processada!")

# Interface Streamlit
st.title("Sistema de Roteirização de Colaboradores")

st.header("Carregue seu(s) arquivo(s) de entrada")
uploaded_files = st.file_uploader("Escolha arquivos", type="txt", accept_multiple_files=True)

if uploaded_files:
    for arquivo in uploaded_files:
        arquivo_path = os.path.join("uploads", arquivo.name)
        with open(arquivo_path, "wb") as f:
            f.write(arquivo.getbuffer())
        
        st.write(f"Processando {arquivo.name}...")
        rotas, coord_x_par, coord_y_par, colaboradores_alocados = solve(arquivo_path)
        st.success(f"Processamento de {arquivo.name} concluído!")
