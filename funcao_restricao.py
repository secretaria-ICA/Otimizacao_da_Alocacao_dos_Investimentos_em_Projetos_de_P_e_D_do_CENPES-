"""
funcao: funcao_restricao(df):

  Objetivo: Verifica as restricoes inerentes as regras de negocio e inclui
            no dataframe passado uma coluna identificando quais contratos
            estao conformes (True) e quais nao estao conformes (False).
            Verifica tambem o atendimento da obrigacao total e inclui uma
            linha "Total Geral" no dataframe, que consolida os valores das
            suas colunas.
             

  Parametros:
              df: dataframe com os valores consolidados de um individuo
                  nos contratos para verificacao das regras de negocio. 
                  

  Retorna:
          df: dataframe passado como parametro de entrada, com:
              - uma coluna incluida, representando o status de conformide
                no atendimento aos contratos;
              - uma linha incluida no final, "Total Geral", que consolida
                os valores das suas colunas.

          individuo_valido: True se o atende a todas as regras de negocio
                            False se nao atende alguma regra de negocio


          (r1_ativo, r2_ativo, r3_ativo): tuple com as series que identificam
                                          cada uma das 3 regras de negocio
                                          ativas para cada contrato.

 Autor: MFB
 Atualizacao: 06/07/2021

"""

import random

# declaracao deconstantes
NUMERO_MIN_PROJETOS_POR_CONTRATO = 1

def funcao_restricao(df):
    # identifica se as regras de negocio de cada contrato estao sendo
    # atendidas, bem como o total da obrigacao.

    # verifica quais regras de negocio estao ativas, preenchidas com
    # algum valor positivo diferente de 0.
    # cria uma serie para cada uma das 3 regras de negocio, identificando
    # como:
    #       True = regra ativa
    #       False = regra NAO esta ativa
    r1_ativo = df["Obrigação - PETROBRAS"] > 0
    r2_ativo = df["Mínimo Externo"] > 0
    r3_ativo = df["Máximo Interno"] > 0

    # verifica a conformidade quanto ao atendimento das regras de negocio,
    # para cada contrato.
    r1 = df["Critério (TOTAL - Obrigação)"] >= 0
    r2 = df["Criterio Mínimo Externo"] >= 0
    r3 = df["Critério Máximo Interno"] >= 0

    # verifica a conformidade da alocacao, representada pelo individuo,
    # quanto ao atendimento de todas as regras de negocio, de todos os
    # contrato.

    # Desconsidera o nao atendimento as regras de negocio que nao estao
    # ativas
    contrato_valido = (r1 | (r1_ativo == False)) & \
                      (r2 | (r2_ativo == False)) & \
                      (r3 | (r3_ativo == False))

    # corrige o status do "Total Geral" para valido caso
    # todos os contratos estejam validos
    individuo_valido = contrato_valido.all()
    contrato_valido[len(contrato_valido) - 1] = individuo_valido

    # insere uma coluna do dataframe, com a status de conformidade no
    # atendimento as regras de negocio para cada contrato
    df["Contrato Conforme ?"] = contrato_valido

    return df, individuo_valido, (r1_ativo, r2_ativo, r3_ativo)


def alocar_contrato(individuo, contrato, numero, indice_contratos):
    # um projeto desalocado e representato pela alocacao em um contrato
    # "vazio", incluido como ultima linha na tabela de indices de contrato
    id_contrato_projeto_nao_alocado = len(indice_contratos)

    # identifica os indices dos projetos que NAO estao alocados
    inds_livres = [index for index, element in enumerate(individuo[:])
                   if element == id_contrato_projeto_nao_alocado]

    # seleciona os indices dos projetos livres a serem alocados no
    # contrato
    if numero < len(inds_livres):
        inds_alocar = random.sample(inds_livres, numero)
    else:
        inds_alocar = inds_livres

    for j in inds_alocar:
        individuo[j] = contrato

    return


def todos_contratos_alocados(individuo, indice_contratos):
    # criar lista com os indices de todos os contratos
    contratos = range(len(indice_contratos))
    # verificar se cada contrato tem ao menos algum projeto alocado
    for contrato in contratos:
        if contrato not in individuo[:]:
            alocar_contrato(individuo, contrato,
                            NUMERO_MIN_PROJETOS_POR_CONTRATO,
                            indice_contratos)

    return

# Exclui da otimizacao os projetos marcados na planilha de entrada
def exclui_projetos(pop, projetos_excluidos, id_contrato_projeto_nao_alocado):
    if len(projetos_excluidos) > 0:
        for ind in pop:
            for i in ind:
                ind[i] = id_contrato_projeto_nao_alocado

    return





def main():
    # definir rotinas de testes para as funcoes do modulo
    return


if __name__ == "__main__":
    main()
