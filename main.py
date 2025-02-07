import os
import glob
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# =============================================================================
# Classe que representa uma rota
# =============================================================================
class Rota:
    def __init__(self, paradas, colaboradores, durationToDepot):
        self.paradas = paradas              
        self.colaboradores = colaboradores  
        self.durationToDepot = durationToDepot  

# =============================================================================
# Função para ler todos os dados da instância
# =============================================================================
def leitortodos(arquivo):
    with open(arquivo, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    first_line = lines[0]
    parts = first_line.split(',')
    p = int(parts[0].split()[0])         
    x = int(parts[1].split()[0])         
    y = int(parts[2].split()[0])         
    e = x + y                           
    dist_max = float(parts[3].split()[0])
    n = int(parts[4].split()[0])
    
    coord_x_par = []
    coord_y_par = []
    for i in range(1, p):
        campos = lines[i].split()
        coord_x_par.append(float(campos[1]))
        coord_y_par.append(float(campos[2]))
    
    coord_x_est = []
    coord_y_est = []
    vecDistMax_input = []
    vecDurMax_input = []
    for i in range(p, p + e):
        campos = lines[i].split()
        coord_x_est.append(float(campos[1]))
        coord_y_est.append(float(campos[2]))
        vecDistMax_input.append(float(campos[3]))
        vecDurMax_input.append(float(campos[4]))
    
    return p, e, n, dist_max, coord_x_par, coord_y_par, coord_x_est, coord_y_est, vecDistMax_input, vecDurMax_input

# =============================================================================
# Função que resolve a heurística e gera as rotas e aloca os colaboradores
# =============================================================================
def solve(arquivo):
    p, e, n, dist_max, coord_x_par, coord_y_par, coord_x_est, coord_y_est, vecDistMax_input, vecDurMax_input = leitortodos(arquivo)
    p = p - 1  
    DistanciaMax = max(vecDistMax_input)
    DuracaoMax = max(vecDurMax_input)
    FatorDist = 1.0
    FatorDur = 1.0

    if e == 0:
        return [], coord_x_par, coord_y_par, {}

    NR_RESTARTS = 10
    best_rotas = []
    best_cost = 1e12  
    best_colaboradores_alocados = {}

    for ms in range(NR_RESTARTS):
        custo_da_solucao = 0.0
        capacidade_veiculo = n
        rotas = []
        colaboradores = list(range(e))
        paradas_visitadas = set()
        paradas_descartadas = set()

        custo = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                if i == j:
                    custo[i, j] = 0.0
                else:
                    custo[i, j] = math.sqrt((coord_x_par[i] - coord_x_par[j])**2 +
                                            (coord_y_par[i] - coord_y_par[j])**2)

        dist = np.zeros((e, p))
        for i in range(e):
            for j in range(p):
                dist[i, j] = math.sqrt((coord_x_est[i] - coord_x_par[j])**2 +
                                       (coord_y_est[i] - coord_y_par[j])**2)

        colaboradores_alocados = dict()

        abortar = False
        abortar2 = False
        while colaboradores:
            if abortar:
                if abortar2:
                    break
                abortar2 = True

            rota_atual = Rota(paradas=[1], colaboradores=[], durationToDepot=[0.0])
            custo_atual = 0.0
            capacidade_atual = 0

            while capacidade_atual < capacidade_veiculo and colaboradores:
                melhor_parada = -1
                melhor_colaboradores = []
                potencial_parada = np.zeros(p)

                for parada in range(2, p + 1):
                    if parada in paradas_visitadas or parada in paradas_descartadas:
                        continue
                    for i in colaboradores:
                        if dist[i, parada - 1] <= min(FatorDist * vecDistMax_input[i], DistanciaMax):
                            if custo[parada - 1, rota_atual.paradas[0] - 1] + rota_atual.durationToDepot[0] <= min(FatorDur * vecDurMax_input[i], DuracaoMax):
                                potencial_parada[parada - 1] += 1

                sorted_indices = np.argsort(potencial_parada)
                random.shuffle(sorted_indices)

                for idx in sorted_indices:
                    if potencial_parada[idx] > 0:
                        proximos = []
                        for i in colaboradores:
                            if dist[i, idx] <= vecDistMax_input[i] or dist[i, idx] <= min(FatorDist * vecDistMax_input[i], DistanciaMax):
                                proximos.append(i)
                        proximos_filtrados = []
                        for i in proximos:
                            duracao = custo[idx, rota_atual.paradas[0] - 1] + rota_atual.durationToDepot[0]
                            if duracao <= vecDurMax_input[i] or duracao <= min(FatorDur * vecDurMax_input[i], DuracaoMax):
                                proximos_filtrados.append(i)
                        if proximos_filtrados:
                            melhor_parada = idx + 1
                            melhor_colaboradores = proximos_filtrados
                            break
                        else:
                            paradas_descartadas.add(idx + 1)

                if melhor_parada == -1:
                    break

                for i in melhor_colaboradores:
                    if capacidade_atual < capacidade_veiculo:
                        rota_atual.colaboradores.append(i)
                        colaboradores.remove(i)
                        capacidade_atual += 1
                        if melhor_parada not in colaboradores_alocados:
                            colaboradores_alocados[melhor_parada] = []
                        colaboradores_alocados[melhor_parada].append(i)
                duracaotemp = custo[melhor_parada - 1, rota_atual.paradas[0] - 1] + rota_atual.durationToDepot[0]
                custo_atual += custo[melhor_parada - 1, rota_atual.paradas[0] - 1]
                rota_atual.paradas.insert(0, melhor_parada)
                rota_atual.durationToDepot.insert(0, duracaotemp)
                paradas_visitadas.add(melhor_parada)

            if rota_atual.paradas[0] != 1:
                rota_atual.paradas.insert(0, 1)
            custo_atual += custo[0, rota_atual.paradas[0] - 1] 
            if not rota_atual.colaboradores:
                break
            rotas.append(rota_atual)
            custo_da_solucao += custo_atual

        if colaboradores:
            for colaborador in colaboradores:
                paradas_validas = list(range(2, p + 1))
                distancias = [dist[colaborador, parada - 1] for parada in paradas_validas]
                if distancias:
                    indice = int(np.argmin(distancias))
                    parada_mais_proxima = paradas_validas[indice]
                    if parada_mais_proxima not in colaboradores_alocados:
                        colaboradores_alocados[parada_mais_proxima] = []
                    colaboradores_alocados[parada_mais_proxima].append(colaborador)
        if custo_da_solucao < best_cost:
            best_cost = custo_da_solucao
            best_rotas = rotas
            best_colaboradores_alocados = colaboradores_alocados

    for rota in best_rotas:
        if rota.paradas[-1] != 1:
            rota.paradas.append(1)

    return best_rotas, coord_x_par, coord_y_par, best_colaboradores_alocados, best_cost

# =============================================================================
# Função Streamlit para upload e exibição dos resultados
# =============================================================================
def app():
    st.title("Resolução de Roteirização de Colaboradores")
    
    uploaded_file = st.file_uploader("Escolha um arquivo de instância", type="txt")
    
    if uploaded_file is not None:
        st.text("Arquivo carregado: " + uploaded_file.name)
        best_rotas, coord_x_par, coord_y_par, best_colaboradores_alocados, best_cost = solve(uploaded_file)

        # Exibição das rotas
        st.subheader("Resultados das Rotas")
        for idx, rota in enumerate(best_rotas, start=1):
            rota_str = " -> ".join(str(s) for s in rota.paradas)
            st.write(f"Rota do veículo {idx}: {rota_str}")
            for parada in rota.paradas:
                if parada != 1 and parada != (len(coord_x_par) + 1):
                    colaboradores_lista = best_colaboradores_alocados.get(parada, [])
                    colaboradores_imprime = " ".join(str(c + 1) for c in colaboradores_lista)
                    st.write(f"Parada {parada} contém os colaboradores: {colaboradores_imprime}")
