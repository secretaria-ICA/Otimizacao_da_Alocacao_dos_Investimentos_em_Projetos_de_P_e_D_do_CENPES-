"""
programa para otimizar a distribuição dos investimentos em
projetos de P&D do CENPES no cumprimento das obrigações legais de
forma eficiente, buscando minimizar o valor excedente desembolsado no
cumprimento de todas as obrigações legais.

    Objetivo: Lê uma planilha padrão "Dados RCA.xlsx" com 2 abas:
               - aba "valores a distribuir", com os valores das
                      projetos disponiveis para serem distribuidos;
               - aba "contratos", com os contratos a serem cumpridos,
                      e suas restricoes de negocio.

    Retorna: Uma planilha "RCA (Projetos X Contratos).xlsx",  com o melhor
             resultado encontrado na alocação dos projetos aos contratos,
             obedecendo todas as regras de negocio, e minimizando o
             excedente de recursos em valor, com 2 abas:
               - aba "distribuição", com as projetos alocados por contrato;
               - aba "consolidacao contratos", com os contratos e os valores
                      consolidados ["Total Empresa", "Total Externo",
                                    "Total Interno", "TOTAL"].

 Autor: MFB
 Atualizacao: 19/07/2021

"""

# Definicao de constantes utilizadas no programa:

# Definicao de constantes e parametros do algoritmo genetico:
NUMERO_GERACOES = 500
TAMANHO_POPULACAO = 100

# de quantas em quantas geracoes guarda o melhor resultado em disco
NUMERO_GERACOES_GRAVA_MELHORES_RESULTADOS = 10
NUMERO_GERACOES_GRAVA_POPULACAO = 10
NUMERO_GERACOES_GRAVA_HISTORICO = 10
NUMERO_MELHORES_INDIVIDUOS_GUARDADO = 500

# define os valores minimos e maximos de cada probabiliade.
# a cada vez sera gerado randomicamente uma probabilidade
# entre os valores minimo e maximo definidos (MIN, MAX)
PROBABILIDADE_CROSSOVER = (0.3, 0.8)
PROBABILIDADE_MUTACAO = (0.3, 0.8)

# Definicao do nomes da planilha de entrada de dados,
# suas abas, nome de colunas criadas em tabelas, etc.
PLANILHA_DADOS_ENTRADA = "Dados RCA.xlsx"
PLANILHA_DADOS_SAIDA = "RCA (Projetos X Contratos).xlsx"
NOME_ABA_ENTRADA_VALORES_A_DISTRIBUIR = "projetos a distribuir"
NOME_ABA_ENTRADA_CONTRATOS = "contratos"
NOME_ABA_SAIDA_DISTRIBUICAO = "distribuição"
NOME_ABA_SAIDA_CONTRATOS_CONSOLIDADOS = "consolidacao contratos"
NOME_COLUNA_CONTRATO = "Contrato"
NOME_ARQUIVO_MELHORES_RESULTADOS = "Melhores_Individuos.rca"
NOME_ARQUIVO_POPULACAO_FINAL = "Populacao_Final.rca"
NOME_ARQUIVO_HISTORICO = "Historico.rca"

import random
import math

# Modulos que tive de adicionar: pandas, openpyxl, xlrd, numpy, deap
# usados pelo QT para a interface grafica: pyside6, pathlib
from deap import base
from deap import creator
from deap import tools
import numpy as np
# importar os outros arquivos do programa
import mutacao
import cruzamento
import selecao
import utilidades as util
import funcao_objetivo as f_obj
import funcao_restricao as negocio

def main():
    # carrega dados de entrada na planilha, e cria as seguintes variaveis
    # com os dados dos contratos e projetos:
    #
    #     df_projetos: dataframe somente com os campos dos dados dos projetos
    #                  necessários para a otimizacao:
    #                  ["Número ANP", "Valor Pago(R$)", "Irá fazer parte do RCA?",
    #                   "Classif", "CONTRATO PRINC"];
    #
    #     df_contratos: dataframe somente com os campos dos dados dos contratos
    #                   necessários para a otimizacao:
    #                   ["Campo", "Obrigação - PETROBRAS", "Mínimo Externo",
    #                    "Mínimo Empresa", "Máximo Interno"]
    #
    #     df_detalhes_projetos = dataframe com todos os campos dos dados dos
    #                            dos projetos, para serem replicados na planilha
    #                            de saida.
    #
    df_projetos, df_detalhes_projetos, projetos_excluidos, df_contratos, \
    df_id_contratos = util.le_planilha_entrada(PLANILHA_DADOS_ENTRADA,
                                               NOME_ABA_ENTRADA_VALORES_A_DISTRIBUIR,
                                               NOME_ABA_ENTRADA_CONTRATOS)

    # declaracoes e configuracoes do DEAP
    fit_weights = f_obj.cria_performance(len(df_id_contratos))
    creator.create("FitnessMin", base.Fitness, weights=fit_weights)
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox = base.Toolbox()

    # Definir o gerador de numeros aleatórios de numeros inteiros entre o
    # intervalo (0 e o número de contratos). sera incluido um
    # "contrato em branco" para representar o caso do projeto
    # nao ter sido alocado em qualquer contrato.
    num_contratos = len(df_id_contratos) - 1
    toolbox.register("attr_int", random.randint, 0, num_contratos)

    # Inicialização do cromossomo (com o numero de genes igual ao numero de
    # projetos a serem alocados)
    num_projetos = len(df_projetos)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_int, n=num_projetos)

    # Registro da populacao, como uma lista de Individuos
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Registro da função objetivo, que alem do individuo, passa as informacoes
    # de contratos e projetos necessarias ao calculo da performance do individuo
    toolbox.register("evaluate", f_obj.funcao_objetivo,
                     indice_contratos=df_id_contratos,
                     contratos=df_contratos,
                     projetos=df_projetos)


    # ### TESTE recupera um individuo valido e grava planilha
    # individuo = util.le_individuo_arquivo("Individuos_Validos.rca")
    # util.grava_planilha_saida(individuo, "Individuos_Validos.xlsx",
    #                           df_id_contratos, df_contratos,
    #                           df_detalhes_projetos)
    #
    # # #########################################################

    # cria a populacao inicial

    # le a ultima populacao salva do arquivo. Caso não encontre,
    # cria uma nova populacao
    pop_salva = util.le_populacao(NOME_ARQUIVO_POPULACAO_FINAL)
    if pop_salva != None:
        pop = pop_salva.items[0:min(TAMANHO_POPULACAO,
                                    len(pop_salva.items))]
    else:
        pop = toolbox.population(n=TAMANHO_POPULACAO)

    # ##########################################
    # se quiser incluir mais uma populacao salva
    # pop_salva = util.le_populacao("Populacao_Final - P 5000.rca")
    # if pop_salva != None
    #     pop = pop + pop_salva.items
    # ##########################################

    # elimina individuos duplicados
    pop_temp = []
    apagados = 0
    for i in pop:
        if i not in pop_temp:
            pop_temp.append(i)
        else:
            apagados += 1
    pop = pop_temp

    # inicializa objeto Hall of Fame do DEAP, para guardar os
    # melhores individuos
    hof_melhores_individuos_geral = \
        tools.HallOfFame(NUMERO_MELHORES_INDIVIDUOS_GUARDADO)

    # inicializa os recursos de estatistica no DEAP:

    # considera apenas os valores de fitness da tabela de performance,
    # ignorando a tabela de desvios
    stats = tools.Statistics(lambda ind:
                             ind.fitness.values[0:int(len(ind.fitness.values) / 2)])
    # registra como "fit" uma variavel que é a soma de todos os valores da
    # tabela de performance. O mesmo que a funcao objetivo.
    stats.register("fit", np.sum, axis=1)

    # inicializa o logbook para guardar o historico das estatisticas
    stats_hist = tools.Logbook()
    stats_hist.header = "ger", "min", "media", "std", "max"

    # Inicio da evolucao
    print("Inicio")

    # Calcular a performance com a funcao objetivo  para
    # todos os individuos da populacao
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    # caso nao queira recalcular as populacoes lidas de arquivo, substitui
    # pelo codigo abaixo:
    # Obs,: caso mude a funcao objetivo, precisam ser recalculados.
    # invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    # fitnesses = map(toolbox.evaluate, invalid_ind)
    # for ind, fit in zip(invalid_ind, fitnesses):
    #     ind.fitness.values = fit

    # loop repetido a cada geracao:
    #
    # a partir de uma populacao:
    #    1 - realiza os cruzamentos;
    #    2 - realiza as mutacoes;
    #    3 - elimina individuos duplicados;
    #    4 - repoe os individuos apagados (com novas mutacoes e cruzamentos);
    #    5 - desaloca projetos excluidos do processo
    #    6 - avalia os individuos com a funcao objetivo;
    #    7 - elimina os individuos que tiveram erro no calculo da funcao
    #        objetivo;
    #    8 - seleciona a populacao da proxima geracao;
    # ################

    # variavel para contar o numero da geracao atual
    g = 0
    while g < NUMERO_GERACOES:
        # Atualiza a contagem da geracao atual
        g = g + 1

        # embaralha a populacao para aumentar a diversidade nos cruzamentos
        # as funcoes de selecao ordenam a populacao por performance
        random.shuffle(pop)

        # 1 - realiza os cruzamentos;

        # seleciona tipo de cruzamento a ser aplicado
        toolbox = cruzamento.tipo(toolbox, num_contratos, df_id_contratos,
                                  df_contratos, df_projetos)

        # realiza os cruzamentos em um percentual da populacao
        mate_list = []
        prob_mate = random.uniform(PROBABILIDADE_CROSSOVER[0],
                                   PROBABILIDADE_CROSSOVER[1])

        for child_1, child_2 in zip(pop[::2], pop[1::2]):
            # Cruza 2 individuos com a probabilidade definida
            # na constante PROBABILIDADE_CROSSOVER
            # Realiza o cruzamento em um percentual dos individuos,
            # com a probabilidade definida randomicamente,
            # entre os limites (minimo e maximo) da
            # constante PROBABILIDADE_MUTACAO
            if random.random() < prob_mate:
                ind_1 = toolbox.clone(child_1)
                ind_2 = toolbox.clone(child_2)
                toolbox.mate(child_1, child_2)
                # Invalida os valores de performance calculados dos novos
                # individuos gerados. Esta performance sera
                # posteriormente calculada com a funcao objetivo
                del child_1.fitness.values
                del child_2.fitness.values
                # inclui na lista dos novos individuos criados
                mate_list.append(ind_1)
                mate_list.append(ind_2)

        # inclui de volta os individuos que foram cruzados na populacao
        pop = pop + mate_list

        # 2 - realiza as mutacoes;

        # seleciona tipo de mutacao
        toolbox = mutacao.tipo(toolbox, numero_contratos=num_contratos,
                               indice_contratos=df_id_contratos,
                               contratos=df_contratos,
                               projetos=df_projetos)

        # nao considera para a mutacao os novos individuos criados
        # que nao tiveram ainda sua performance calculdada
        valid_ind = [ind for ind in pop if ind.fitness.valid]
        mutant_list = []
        # Realiza a mutacao em um percentual dos individuos com a
        # probabilidade definida randomicamente, entre os limites
        # (minimo e maximo) da constante PROBABILIDADE_MUTACAO
        prob_mut = random.uniform(PROBABILIDADE_MUTACAO[0],
                                  PROBABILIDADE_MUTACAO[1])
        for mutant in valid_ind:
            if random.random() < prob_mut:
                ind = toolbox.clone(mutant)
                toolbox.mutate(mutant)
                # invalida o fitness do novo individuo gerado, para que
                # sua performance seja calculada posteriormente
                del ind.fitness.values
                # inclui na lista dos novos individuos criados
                mutant_list.append(ind)

        # inclui de volta os individuos que sofreram mutacao na populacao,
        pop = pop + mutant_list

        # 3 - elimina individuos duplicados;
        pop_temp = []
        apagados = 0
        for i in pop:
            if i not in pop_temp:
                pop_temp.append(i)
            else:
                apagados += 1
        pop = pop_temp

        # print("apagados ", apagados)

        # mantem o tamanho da populacao, evitando que reduza por
        # motivo de individuos duplicados ou criados com performance
        # invalida, que foram apagados
        apagados = max(apagados, TAMANHO_POPULACAO-len(pop))
        # print("repor ", apagados)

        # 4 - repoe os individuos apagados (com novas mutacoes e cruzamentos);
        # criados aleatoriamente por cruzamento e mutacao
        lista_novos = []
        repostos = 0
        # nao considera para a mutacao ou cruzamento os novos individuos
        # criados que ainda nao tiveram ainda sua performance calculada
        valid_ind = [ind for ind in pop if ind.fitness.valid]
        # print("inicio reposicao da populacao")
        duplicados = 0
        while len(valid_ind) > 0 and apagados > 0:
            # seleciona randomicamente criar por mutacao ou cruzamento
            # Ajusta a probabilidade considerando:
            #  - cada mutacao gera 1 individuo e cada cruzamento gera 2
            #  - as probabilidades de mutacao e cruzamento desta geracao
            if random.random() < (2/3)*(prob_mut/prob_mate):
                if len(valid_ind) < 1:
                    # sai do loop caso não tenha individuos validos suficiente
                    break
                # criar por mutacao
                mutant = random.sample(valid_ind, 1)[0]
                ind = toolbox.clone(mutant)
                toolbox.mutate(mutant)
                # Invalida os valores calculados de fitness para que seja
                # calculada a performance do novo individuo
                del mutant.fitness.values
                # inclui na lista dos novos individuos criados
                lista_novos.append(ind)
            else:
                if len(valid_ind) < 2:
                    # sai do loop caso não tenha individuos validos suficiente
                    break
                # criar por cruzamento
                child_1, child_2 = random.sample(valid_ind, 2)
                ind_1 = toolbox.clone(child_1)
                ind_2 = toolbox.clone(child_2)
                toolbox.mate(child_1, child_2)
                # Invalida os valores calculados de fitness para que seja
                # calculada a performance do novo individuo
                del child_1.fitness.values
                del child_2.fitness.values
                # inclui na lista de novos individuos criados
                lista_novos.append(ind_1)
                lista_novos.append(ind_2)

            # inclui novos individuos criados na populacao, caso nao seja
            # um individuo duplicado
            for i in lista_novos:
                if i not in pop:
                    pop.append(i)
                    repostos += 1
                    apagados -= 1
                else:
                    duplicados += 1
            lista_novos = []

            # nao considera para a mutacao ou cruzamento os
            # novos individuos criados que nao tiveram ainda
            # sua performance calculdada
            valid_ind = [ind for ind in pop if ind.fitness.valid]

        # print("criados duplicados ", duplicados)
        # print("repostos ", repostos)

        # 5 - desaloca projetos excluidos do processo para os novos individuos

        # um projeto desalocado e representato pela alocacao em um contrato
        # "vazio", incluido como ultima linha na tabela de indices de contrato
        id_contrato_projeto_nao_alocado = len(df_id_contratos)
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        # ### ATENCAO ### ainda nao implementado
        negocio.exclui_projetos(invalid_ind, projetos_excluidos,
                                id_contrato_projeto_nao_alocado)

        # 6 - avalia os novos individuos com a funcao objetivo;

        # Calcular a performance de todos os novos individuos gerados,
        # que tiveram seus fitness invalidados no cruzamento e mutacao.
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # 7 - elimina os individuos que tiveram erro no calculo
        #     da funcao objetivo;

        # ### ATENCAO ### descobrir porque estao sendo criados para
        # nao precisar eliminar
        pop_temp = []
        performance_invalida = 0
        for i in pop:
            if not math.isnan(f_obj.performance(i)):
                pop_temp.append(i)
            else:  # Aqui identifica quando um individuo
                   # com performance invalida foi identificado e apagado.
                performance_invalida += 1
        pop = pop_temp
        # print("apagados por performance invalida ", performance_invalida)

        # 8 - seleciona a populacao da proxima geracao;

        # define o tipo de selecao de individuos usado.
        toolbox = selecao.tipo(toolbox, numero_contratos=num_contratos,
                               indice_contratos=df_id_contratos,
                               contratos=df_contratos,
                               projetos=df_projetos)

        # realiza a funcao de selecao definida
        pop = toolbox.select(pop, TAMANHO_POPULACAO)
        # Clona os individuos da proxima geracao
        pop = list(map(toolbox.clone, pop))

        # calcula as estatisticas e guarda no historico
        record = stats.compile(pop)
        stats_hist.record(ger=g, min=np.min(record['fit']),
                          media=np.mean(record['fit']),
                          std=np.std(record['fit']),
                          max=np.max(record['fit']))

        print("Geração %i - Avaliados %i" % (g, len(invalid_ind)))

        # ### ATENCAO ### considera que a funcao de selecao utilizada devolveu
        # a populacao ordenada por performance. So as funcoes de selecao
        # customizadas em selecao.py fazem isso.
        # melhor_individuo_geracao = tools.selBest(pop, 1)[0]
        melhor_individuo_geracao = toolbox.clone(pop[0])
        performance_melhor_individuo_geracao = \
            f_obj.performance(melhor_individuo_geracao)

        # criar a variavel para guardar o melhor individuo geral
        # na primeira geracao
        if g == 1:
            melhor_individuo_geral = toolbox.clone(melhor_individuo_geracao)
            performance_melhor_individuo_geral = \
                performance_melhor_individuo_geracao

        # guarda o melhor individuo geral, e substitui, caso
        # sua performance seja invalida ### ATENCAO ### ver porque
        # pode assumir performance invalida
        if math.isnan(performance_melhor_individuo_geral):
            melhor_individuo_geral = toolbox.clone(melhor_individuo_geracao)
            performance_melhor_individuo_geral = \
                performance_melhor_individuo_geracao
        if performance_melhor_individuo_geracao < \
                performance_melhor_individuo_geral:
            melhor_individuo_geral = toolbox.clone(melhor_individuo_geracao)
            performance_melhor_individuo_geral = \
                performance_melhor_individuo_geracao

        hof_melhores_individuos_geral.insert(melhor_individuo_geral)
        # melhor_individuo_geral = hof_melhores_individuos_geral[0]

        # grava o melhor individuo em arquivo e planilha
        if g >= NUMERO_GERACOES_GRAVA_MELHORES_RESULTADOS and \
                (g % NUMERO_GERACOES_GRAVA_MELHORES_RESULTADOS) == 1:
            # grava melhor individuo geral em arquivo
            util.grava_individuo(NOME_ARQUIVO_MELHORES_RESULTADOS,
                                 melhor_individuo_geral)
            # grava planilha de saida com o melhor resultado ate agora
            util.grava_planilha_saida(melhor_individuo_geral,
                                      PLANILHA_DADOS_SAIDA,
                                      df_id_contratos, df_contratos,
                                      df_detalhes_projetos)

            # atualiza o hall of fame dos melhores individuos
            # hof_melhores_individuos_geral.update(pop)

        # grava a populacao em arquivo para permitir ser recuperada
        # e continuar a otimizacao posteriormente
        if g >= NUMERO_GERACOES_GRAVA_POPULACAO and \
                (g % NUMERO_GERACOES_GRAVA_POPULACAO) == 1:
            hof_populacao = tools.HallOfFame(TAMANHO_POPULACAO)
            hof_populacao.update(pop)
            util.grava_populacao(NOME_ARQUIVO_POPULACAO_FINAL,
                                 hof_populacao)

        # grava arquivo historico das etatisticas em arquivo
        if g >= NUMERO_GERACOES_GRAVA_HISTORICO and\
                (g % NUMERO_GERACOES_GRAVA_HISTORICO) == 1:
                util.grava_historico(NOME_ARQUIVO_HISTORICO, stats_hist)


        # imprime melhores resultados na tela
        print("   Melhor = " +
              '{:,.0f}'.format(performance_melhor_individuo_geral) +
              "  Média = " +
              '{:,.0f}'.format(stats_hist.select('media')[-1]) +
              "  Desvio = " +
              '{:,.0f}'.format(stats_hist.select('std')[-1]))

    # Finaliza o programa, gravando arquivos, planilhas e print na tela
    if g > 0:  # o algoritmo genetico foi executado
        print("-- Final com sucesso  --")

        # cria a planilha de saida, e grava o melhor resultado
        print("Melhor resultado geral =  ",
              '{:,.0f}'.format(f_obj.performance(melhor_individuo_geral)),
              util.grava_planilha_saida(melhor_individuo_geral,
                                        PLANILHA_DADOS_SAIDA, df_id_contratos,
                                        df_contratos, df_detalhes_projetos))

        # Salva em disco a ultima populacao para permitir continuar
        # a otimizacao posteriormente
        hof_populacao_final = tools.HallOfFame(TAMANHO_POPULACAO)
        hof_populacao_final.update(pop)
        util.grava_populacao(NOME_ARQUIVO_POPULACAO_FINAL, hof_populacao_final)

        # grava arquivo historico das etatisticas em arquivo
        util.grava_historico(NOME_ARQUIVO_HISTORICO, stats_hist)


if __name__ == "__main__":
    main()
