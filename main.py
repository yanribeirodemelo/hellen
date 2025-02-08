import os
import glob
import math
import random
import re
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image

# =============================================================================
# Interface Streamlit
# =============================================================================

st.set_page_config(page_title="Sistema de Roteirização", page_icon="pmd.png", layout="wide")

def main():
    #criando 3 colunas
    col1, col2, col3 = st.columns(3)
    foto = Image.open('ufpe.png')
    #foto = foto.resize((75, 150))
    #inserindo na coluna 2
    col2.image(foto, use_container_width=True)
    
    
    st.title('Sistema de Roteirização para Colaboradores')

    menu = ["Aplicação", "Informações"]

    choice = st.sidebar.selectbox("Selecione aqui", menu)
    
    if choice == menu[0]:
        
        st.header(menu[0])
        
        # =============================================================================
        # Classe que representa uma rota
        # =============================================================================
        class Rota:
            def __init__(self, paradas, colaboradores, durationToDepot):
                self.paradas = paradas              # lista de paradas (1-baseado)
                self.colaboradores = colaboradores  # lista de colaboradores (estudantes) alocados nesta rota
                self.durationToDepot = durationToDepot  # lista de tempos acumulados até o depósito
        
        # =============================================================================
        # Função para ler todos os dados da instância
        # =============================================================================
        def leitortodos(arquivo):
            with open(arquivo, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            first_line = lines[0]
            parts = first_line.split(',')
            p = int(parts[0].split()[0])         # número de stops (contando o depósito – isto vem como 21)
            x = int(parts[1].split()[0])         # número de old_students
            y = int(parts[2].split()[0])         # número de new_students
            e = x + y                           # total de estudantes
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
        
            st.subheader("Solução")
            # Impressão do resultado esperado
            for idx, rota in enumerate(best_rotas, start=1):
                rota_str = " ".join(str(s) for s in rota.paradas)
                st.write(f"-> Rota do veículo {idx}: {rota_str}")
                for parada in rota.paradas:
                    # Na saída Julia, não se imprime o depósito (1) nem o último (length(coord_x_par)+1)
                    if parada != 1 and parada != (len(coord_x_par) + 1):
                        colaboradores_lista = best_colaboradores_alocados.get(parada, [])
                        # Converter os índices de colaboradores para 1-base (somamos 1)
                        colaboradores_imprime = " ".join(str(c + 1) for c in colaboradores_lista)
                        st.write(f"Parada {parada} contém os colaboradores: {colaboradores_imprime}")
                st.write()
            st.write(f"Melhor custo encontrado: {best_cost:.3f} (em unidades de comprimento).")
            return best_rotas, coord_x_par, coord_y_par, best_colaboradores_alocados, best_cost, coord_x_est, coord_y_est
        
        def plotar_rotas(rotas, coord_x_par, coord_y_par, colaboradores_alocados, coord_x_est, coord_y_est):
            # Criar a figura e os eixos
            fig, ax = plt.subplots(figsize=(10, 8))
        
            # Plote as paradas
            ax.scatter(coord_x_par, coord_y_par, c='lightgray', label='Paradas', marker='o')
            ax.scatter([50.0], [50.0], color='gray', s=200)  # Centro (depósito)
        
            # Plote as alocações dos colaboradores
            for parada, colaboradores in colaboradores_alocados.items():
                # Coleta as coordenadas da parada
                parada_idx = parada - 1  # Para ajustar o índice da parada
                x_parada = coord_x_par[parada_idx]
                y_parada = coord_y_par[parada_idx]
                
                # Plote os colaboradores
                for colaborador in colaboradores:
                    x_est = coord_x_est[colaborador]
                    y_est = coord_y_est[colaborador]
                    ax.plot([x_est, x_parada], [y_est, y_parada], c='black', linestyle='--')  # Linha pontilhada entre colaborador e a parada
                    ax.scatter(x_est, y_est, color='#D3D3D3', s=50)  # Ponto cinza claro (tamanho ajustável)
        
            # Plote as rotas (linhas conectando as paradas)
            for idx, rota in enumerate(rotas, start=1):  # Começa a contagem do índice das rotas em 1
                paradas = rota.paradas
                x_rotas = [coord_x_par[parada - 1] for parada in paradas]  # Ajusta os índices das paradas
                y_rotas = [coord_y_par[parada - 1] for parada in paradas]
                ax.plot(x_rotas, y_rotas, label=f'Rota do veículo {idx}')  # Inclui o número do veículo na legenda
        
            # Ajuste do gráfico
            ax.set_xlim(0, 100)  # Define a escala do eixo x
            ax.set_ylim(0, 100)  # Define a escala do eixo y
            ax.spines['top'].set_visible(False)  # Remove o eixo superior
            ax.spines['right'].set_visible(False)  # Remove o eixo direito
            ax.xaxis.set_ticks_position('bottom')  # Define que os ticks do eixo x aparecem na parte inferior
            ax.yaxis.set_ticks_position('left')  # Define que os ticks do eixo y aparecem na parte esquerda
        
            ax.legend(loc='best')
        
            # Exibindo a figura no Streamlit
            st.subheader("Visualização Gráfica")
            st.pyplot(fig)

        
        # Upload de arquivo
        uploaded_file = st.file_uploader("Faça upload do seu arquivo de entrada", type=["txt"])
        
        if uploaded_file is not None:
            # Salvar o arquivo temporariamente
            with open('input.txt', 'wb') as f:
                f.write(uploaded_file.read())
        
            # Executar a solução
            rotas, coord_x_par, coord_y_par, colaboradores_alocados, best_cost, coord_x_est, coord_y_est = solve('input.txt')
        
            # Plotar as rotas
            plotar_rotas(rotas, coord_x_par, coord_y_par, colaboradores_alocados, coord_x_est, coord_y_est)

    if choice == menu[1]:
        st.header(menu[1])
        st.write('''Este aplicativo foi desenvolvido pela mestranda Hellen Souza do Programa de Pós-graduação em Engenharia de Produção da Universidade Federal de Pernambuco, sob a orientação do Dr. Raphael Kramer, com o objetivo de otimizar a roteirização de colaboradores em empresas que lidam com atividades logísticas dinâmicas. No qual é especialmente útil para empresas que necessitam gerenciar a contratação de novos funcionários e coordenar operações de forma eficiente, adaptando-se rapidamente a mudanças nas necessidades logísticas.''')
        st.write('''hellen.souza@ufpe.br''')
        st.write('''raphael.kramer@ufpe.br''')
        
main()
