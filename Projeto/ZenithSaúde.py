import heapq 
import random          
import numpy as np     #gerar valores aleatórios segundo distribuições estatísticas
import json
import matplotlib.pyplot as plt
import FreeSimpleGUI as sg

def carregarBD(nome_ficheiro):
    with open(nome_ficheiro, "r", encoding="utf-8") as f:
        return json.load(f)

pessoas = carregarBD("pessoas.json")

# Parâmetros da aplicação
# ---
NUM_MEDICOS = 3           #disponíveis
TAXA_CHEGADA = 10 / 60    # 10 doentes por h -> para min
TEMPO_MEDIO_CONSULTA = 15 
TEMPO_SIMULACAO = 8 * 60  # aprox 8h
DISTRIBUICAO_TEMPO_CONSULTA = "exponential"

ESPECIALIDADES = ["cardiologia", "ortopedia", "neurologia"]
PRIORIDADES = {"vermelho": 0, "amarelo": 1, "verde": 2} # menor número = maior prioridade

CHEGADA = "chegada"
SAIDA = "saída"

DESISTENCIA = "desistência"
TEMPO_MAX_ESPERA = {"vermelho": float("inf"), "amarelo": 60, "verde": 30}


# --- Modelo para o evento (cd um é um tuplo)
# Evento = (tempo: Float, tipo: String, doente: String)
# --- Funções de manipulação
def e_tempo(e):
    return e[0]

def e_tipo(e):
    return e[1]

def e_doente(e):
    return e[2]

# Médicos

class Medico:
    def __init__(self, id, especialidade):
        self.id = id
        self.especialidade = especialidade
        self.ocupado = False
        self.doente_corrente = None
        self.total_tempo_ocupado = 0.0
        self.inicio_ultima_consulta = 0.0

    def iniciar_consulta(self, doente, tempo_atual):
        self.ocupado = True
        self.doente_corrente = doente
        self.inicio_ultima_consulta = tempo_atual

    def terminar_consulta(self, tempo_atual):
        self.ocupado = False
        tempo_fim = min(tempo_atual, TEMPO_SIMULACAO)
        self.total_tempo_ocupado += tempo_fim - self.inicio_ultima_consulta
        self.doente_corrente = None

# Doentes 

class Doente:
    def __init__(self, id, nome, especialidade, prioridade):
        self.id = id
        self.nome = nome
        self.especialidade = especialidade
        self.prioridade = prioridade

# --- Utilização das distribuições para gerar chegadas e durações das consultas

def gera_intervalo_tempo_chegada(lmbda):
    return np.random.exponential(1 / lmbda) #poisson

def gera_tempo_consulta():
    if DISTRIBUICAO_TEMPO_CONSULTA == "exponential":
        return np.random.exponential(TEMPO_MEDIO_CONSULTA)
    elif DISTRIBUICAO_TEMPO_CONSULTA == "normal":
        return max(0, np.random.normal(TEMPO_MEDIO_CONSULTA, 5))
    elif DISTRIBUICAO_TEMPO_CONSULTA == "uniform":
        return np.random.uniform(TEMPO_MEDIO_CONSULTA * 0.5, TEMPO_MEDIO_CONSULTA * 1.5)

# --- Funções auxiliares

# --- Procura o primeiro médico livre e da especialidade certa


def procuraMedicoEspecialidade(medicos, especialidade):
    medico = None
    encontrado = False
    i = 0

    while i < len(medicos) and not encontrado: #percorre a lista de médicos
        if (not medicos[i].ocupado and medicos[i].especialidade == especialidade): #procura um medico livre e se tem a especialidade requerida
            medico = medicos[i]
            encontrado = True #retorna o primeiro que encontra ou none
        i += 1

    return medico

# --- Prioridade na fila de espera ----------------

def escolhe_doente_fila(queue, doentes, especialidade_medico):
    melhor = None
    ind = None

    for i, (prio, t, did) in enumerate(queue): 
        d = doentes[did]
        if d.especialidade == especialidade_medico: 
            if melhor is None or (prio, t) < melhor:
                melhor = (prio, t)                   # com > prioridade e que chegou + cedo
                ind = i

    if ind is not None:
        return queue.pop(ind) # retira doente da queue
    return None

# ---- Calcular fila média ------

def calcula_fila_media_tempo(historico_fila, tempo_simulacao):
    if len(historico_fila) < 2:
        return 0

    area = 0

    for i in range(len(historico_fila) - 1):
        t_atual, tamanho = historico_fila[i]
        t_prox, _ = historico_fila[i + 1]

        duracao = t_prox - t_atual
        area += tamanho * duracao

    return area / tempo_simulacao

# ---- Contar Médicos ocupados ----

def conta_medicos_ocupados(medicos):
    return sum(1 for m in medicos if m.ocupado)


# Gráficos ----------------

# Evolução do tamanho da fila ao longo do tempo

def grafico_evolucao_fila(historico_fila):
    if not historico_fila:
        print("Sem dados para o gráfico da fila.")
        return

    tempos = [t for t, _ in historico_fila]
    tamanhos = [tam for _, tam in historico_fila]

    plt.figure()
    plt.plot(tempos, tamanhos)
    plt.xlabel("Tempo (minutos)")
    plt.ylabel("Tamanho da fila de espera")
    plt.title("Evolução do tamanho da fila ao longo do tempo")
    plt.grid(True)
    plt.show

# Ocupação dos médicos durante a simulação

def grafico_ocupacao_medicos(medicos):
    nomes = []
    ocupacoes = []
    cores = []
    labels = []

    mapa_cores = {
        "cardiologia": "darkred",
        "ortopedia": "rebeccapurple",
        "neurologia": "forestgreen"
    }

    especialidades_usadas = set()

    for m in medicos:
        nomes.append(f"{m.id}\n({m.especialidade})")
        ocupacao = (m.total_tempo_ocupado / TEMPO_SIMULACAO) * 100
        ocupacoes.append(ocupacao)
        cores.append(mapa_cores.get(m.especialidade, "gray"))

        if m.especialidade not in especialidades_usadas:
            labels.append(m.especialidade.capitalize())
            especialidades_usadas.add(m.especialidade)
        else:
            labels.append(None)

    plt.figure()
    plt.bar(nomes, ocupacoes, color=cores, label=labels)

    plt.xlabel("Médicos")
    plt.ylabel("Ocupação (%)")
    plt.title("Ocupação dos médicos durante a simulação")
    plt.ylim(0, 100)
    plt.grid(axis="y")

    plt.legend()
    plt.show

# Tamanho médio da fila vs Taxa de chegada (λ)

def grafico_fila_media_vs_lambda(lambdas):
    global TAXA_CHEGADA

    filas_medias = []
    taxa_original = TAXA_CHEGADA

    for lmbda in lambdas:
        TAXA_CHEGADA = lmbda / 60  # converter de doentes/hora para por minuto
        resultados = simula()
        fila_media = resultados["fila_media"]
        filas_medias.append(fila_media)

    TAXA_CHEGADA = taxa_original

    plt.figure()
    plt.plot(lambdas, filas_medias, marker="o")
    plt.xlabel("Taxa de chegada λ (doentes/hora)")
    plt.ylabel("Tamanho médio da fila")
    plt.title("Tamanho médio da fila vs Taxa de chegada (λ)")
    plt.grid(True)
    plt.show

# Tempo médio de espera de prioridade

def grafico_tempo_medio_espera_prioridade(tempos_espera_prioridade):
    prioridades = ["vermelho", "amarelo", "verde"]
    cores = ["red", "yellow", "green"]
    tempos_medios = []

    for p in prioridades:
        if tempos_espera_prioridade[p]:
            media = sum(tempos_espera_prioridade[p]) / len(tempos_espera_prioridade[p])
        else:
            media = 0
        tempos_medios.append(media)

    plt.figure()
    plt.bar(prioridades, tempos_medios, color=cores)
    plt.xlabel("Prioridade")
    plt.ylabel("Tempo médio de espera (minutos)")
    plt.title("Tempo médio de espera por prioridade")
    plt.grid(axis="y")
    plt.show

# Desistências acumuladas ao longo do tempo

def grafico_desistencias_tempo(historico_desistencias):
    if not historico_desistencias:
        print("Não houve desistências.")
        return

    tempos = [t for t, _ in historico_desistencias]
    acumulado = [d for _, d in historico_desistencias]

    plt.figure()
    plt.step(tempos, acumulado, where="post")
    plt.xlabel("Tempo (minutos)")
    plt.ylabel("Número de desistências")
    plt.title("Desistências acumuladas ao longo do tempo")
    plt.grid(True)
    plt.show

# Ocupação de médicos ao longo do tempo

def grafico_ocupacao_ao_longo_do_tempo(historico_ocupacao):
    if not historico_ocupacao:
        print("Sem dados de ocupação.")
        return

    tempos = [t for t, _ in historico_ocupacao]
    ocupados = [o for _, o in historico_ocupacao]

    plt.figure()
    plt.step(tempos, ocupados, where="post")
    plt.xlabel("Tempo (minutos)")
    plt.ylabel("Número de médicos ocupados")
    plt.title("Ocupação dos médicos ao longo do tempo")
    plt.grid(True)
    plt.show

# -------- FUNÇÃO PRINCIPAL ---------------------------------

def simula():
    tempo_atual = 0.0 #estado inicial da simulação
    queueEventos = [] # Lista de eventos que vão acontecer, ordenada por tempo de ocorrência do evento
    queue = []        
    tempos_chegada= {}
    tempos_inicio_consulta= {}
    tempos_espera= {}
    tempos_sistema = {}
    historico_fila = []
    historico_doentes_fila = []
    historico_fila_detalhado = []
    historico_desistencias = []
    historico_ocupacao = []
    estado_doentes = {}
    tempos_espera_prioridade = {"vermelho": [], "amarelo": [], "verde": []}
    pessoas_disponiveis = pessoas.copy()
    random.shuffle(pessoas_disponiveis)

    medicos = []
    especialidades_medicos = []

    # garante pelo menos um médico por especialidade
    if NUM_MEDICOS >= len(ESPECIALIDADES):
        especialidades_medicos.extend(ESPECIALIDADES)

    # preenche os restantes aleatoriamente
    while len(especialidades_medicos) < NUM_MEDICOS:
        especialidades_medicos.append(random.choice(ESPECIALIDADES))

    random.shuffle(especialidades_medicos)

    # cria os médicos
    for i, esp in enumerate(especialidades_medicos):
        medicos.append(Medico(f"m{i}", esp))


    # --- Geração das chegadas de doentes

    chegadas = {}    
    tempo_atual = gera_intervalo_tempo_chegada(TAXA_CHEGADA)
    while tempo_atual < TEMPO_SIMULACAO and pessoas_disponiveis:

        pessoa = pessoas_disponiveis.pop()

        id_doente = pessoa["id"]
        nome_doente = pessoa["nome"]
        esp = random.choice(ESPECIALIDADES)
        cor = random.choices(["vermelho", "amarelo", "verde"], weights=[0.15, 0.35, 0.50])[0]
        doente = Doente(id_doente, nome_doente, esp, cor)
        
        chegadas[doente.id] = doente
        tempos_chegada[doente.id] = tempo_atual
        heapq.heappush(queueEventos, (tempo_atual, CHEGADA, doente.id))    
        tempo_atual += gera_intervalo_tempo_chegada(TAXA_CHEGADA)


    # --- Tratamento dos eventos
    
    doentes_atendidos = 0
    desistencias = 0

    while queueEventos:
        evento = heapq.heappop(queueEventos)
        tipo = e_tipo(evento)
        id_doente = e_doente(evento)
        tempo_atual = e_tempo(evento)
        historico_fila.append((tempo_atual, len(queue)))

        if tipo == CHEGADA:
            
            doente=chegadas[id_doente]

            estado_doentes[id_doente] = {
                "nome": doente.nome,
                "especialidade": doente.especialidade,
                "prioridade": doente.prioridade,
                "chegada": tempo_atual,
                "inicio": None,
                "saida": None,
                "estado": "Em espera"
            }

            print(
                f"CHEGADA | {doente.nome} ({doente.id}) | "
                f"Especialidade: {doente.especialidade} | "
                f"Prioridade: {doente.prioridade} | "
                f"Tempo: {tempo_atual:.2f}"
            )
            
            medico = procuraMedicoEspecialidade(medicos, doente.especialidade)

            if medico is not None: #se sim
                medico.iniciar_consulta(doente.id,tempo_atual) #inicia se a consulta
                historico_ocupacao.append((tempo_atual, conta_medicos_ocupados(medicos)))
                tempos_inicio_consulta[doente.id] = tempo_atual 
                tempo_consulta = gera_tempo_consulta()
                estado_doentes[id_doente]["inicio"] = tempo_atual
                estado_doentes[id_doente]["estado"] = "Em consulta"
                
                tempos_espera[doente.id] = ( tempos_inicio_consulta[doente.id] - tempos_chegada[doente.id])
                tempos_espera_prioridade[doente.prioridade].append(tempo_atual - tempos_chegada[doente.id])
                
                heapq.heappush(queueEventos,(tempo_atual + tempo_consulta, SAIDA, doente.id)) #agenda-se evento de saída
            
            else:
                queue.append((PRIORIDADES[doente.prioridade], tempo_atual, doente.id))
                historico_doentes_fila.append((tempo_atual, doente.id, doente.nome, doente.especialidade, doente.prioridade))
                if doente.prioridade != "vermelho":
                    tempo_desistencia = tempo_atual + TEMPO_MAX_ESPERA[doente.prioridade]
                    heapq.heappush(queueEventos, (tempo_desistencia, DESISTENCIA, doente.id))

                historico_fila.append((tempo_atual, len(queue)))
                fila_ids = [did for _, _, did in queue]
                historico_fila_detalhado.append((tempo_atual,fila_ids.copy()))

                print(f"Fila de Espera({len(queue)}): ", queue)
        
        
        elif tipo == DESISTENCIA:

            # verificar se o doente ainda está na fila
            ind = None
            i = 0

            while i < len(queue) and ind is None:
                if queue[i][2] == e_doente(evento):
                    ind = i
                i += 1

            if ind is not None:
                doente = chegadas[id_doente]
                tempo_espera = tempo_atual - tempos_chegada[id_doente]
                tempos_espera_prioridade[doente.prioridade].append(tempo_espera)

                print(
                f"DESISTÊNCIA | {doente.nome} ({doente.id}) | "
                f"Especialidade: {doente.especialidade} | "
                f"Prioridade: {doente.prioridade} | "
                f"Tempo: {tempo_atual:.2f}"
            )
                
                queue.pop(ind)
                desistencias += 1
                historico_desistencias.append((tempo_atual, desistencias))
                historico_fila.append((tempo_atual, len(queue)))
                fila_ids = [did for _, _, did in queue]
                estado_doentes[id_doente]["estado"] = "Desistiu"
                estado_doentes[id_doente]["saida"] = tempo_atual
                historico_fila_detalhado.append((tempo_atual,fila_ids.copy()))       

        elif tipo == SAIDA:

            doente = chegadas[id_doente]

            print(
                f"SAÍDA | {doente.nome} ({doente.id}) | "
                f"Especialidade: {doente.especialidade} | "
                f"Prioridade: {doente.prioridade} | "
                f"Tempo: {tempo_atual:.2f}"
            )

            tempos_sistema[id_doente] = (tempo_atual - tempos_chegada[id_doente])
            estado_doentes[id_doente]["saida"] = tempo_atual
            estado_doentes[id_doente]["estado"] = "Atendido"  # Vamos libertar o médico e despachar o doente

            
            doentes_atendidos += 1
            medico = None  
            encontrado = False
            i = 0
            while i < len(medicos) and not encontrado:
                if medicos[i].doente_corrente == e_doente(evento): # procura medico que atendeu o doente
                    medico = medicos[i]
                    encontrado = True
                i += 1
                
            medico.terminar_consulta(tempo_atual) 
            historico_ocupacao.append((tempo_atual, conta_medicos_ocupados(medicos)))
            
            if queue != []: # se há doentes à espera vou ocupar o médico que ficou livre...

                resultado = escolhe_doente_fila(queue, chegadas, medico.especialidade)

                if resultado: # doente já saiu da fila
                    historico_fila.append((tempo_atual, len(queue)))
                    fila_ids = [did for _, _, did in queue]
                    historico_fila_detalhado.append((tempo_atual,fila_ids.copy()))
                    prio, t_chegada, did = resultado
                    medico.iniciar_consulta(did, tempo_atual) 
                    historico_ocupacao.append((tempo_atual, conta_medicos_ocupados(medicos)))
                    estado_doentes[did]["inicio"] = tempo_atual
                    estado_doentes[did]["estado"] = "Em consulta"

                    tempo_espera = tempo_atual - tempos_chegada[did]
                    tempos_espera[did] = tempo_espera
                    novo_doente = chegadas[did]
                    tempos_espera_prioridade[novo_doente.prioridade].append(tempo_espera)

                    tempos_inicio_consulta[did] = tempo_atual 
                    tempos_espera[did] = tempo_atual - tempos_chegada[did]

                    tempo_consulta = gera_tempo_consulta()
                    heapq.heappush(queueEventos, (tempo_atual + tempo_consulta, SAIDA, did))
                    

    print(f"Doentes atendidos: {doentes_atendidos}") 
    print(f"Doentes que desistiram: {desistencias}")

    
    media_espera = (sum(tempos_espera.values()) / len(tempos_espera) if tempos_espera else 0)
    media_sistema = (sum(tempos_sistema.values()) / len(tempos_sistema) if tempos_sistema else 0)
    print("\nOcupação dos médicos:")

    for m in medicos:
        ocupacao = (m.total_tempo_ocupado / TEMPO_SIMULACAO) * 100
        print(f"Médico {m.id} ({m.especialidade}): {ocupacao:.1f}%")

    if historico_fila:
        tamanhos = [tam for _, tam in historico_fila]
        fila_media = calcula_fila_media_tempo(historico_fila, TEMPO_SIMULACAO)
        fila_max = max(tamanhos)
    else:
        fila_media= 0
        fila_max= 0
        
    print(f"Tempo médio de espera: {media_espera:.2f} minutos") # .2f - mostra até duas casas decimais
    print(f"Tempo médio na clínica: {media_sistema:.2f} minutos")
    print(f"Tamanho médio da fila: {fila_media:.2f}")
    print(f"Tamanho máximo da fila: {fila_max}")

    return {
    "fila_media": fila_media,
    "fila_max": fila_max,
    "media_espera": media_espera,
    "media_sistema": media_sistema,
    "doentes_atendidos": doentes_atendidos,
    "desistencias": desistencias,
    "medicos": medicos,
    "doentes": chegadas,
    "historico_fila": historico_fila,
    "historico_doentes_fila": historico_doentes_fila,
    "historico_fila_detalhado": historico_fila_detalhado,
    "historico_desistencias": historico_desistencias,
    "tempos_espera_prioridade": tempos_espera_prioridade,
    "historico_ocupacao": historico_ocupacao,
    "estado_doentes": estado_doentes
}


# =================================================================
# 3. INTERFACE 
# =================================================================

# TEMA GERAL
sg.theme_background_color("#0F2A44")
sg.theme_element_background_color("#163A5F")
sg.theme_text_color("#EAF6F6")

sg.theme_input_background_color("#1F4B6E")
sg.theme_input_text_color("#EAF6F6")

sg.theme_button_color(("#0F2A44", "#4DB6AC"))

users = carregarBD("users.json")

layout_login = [
    [
        sg.Image(
            "logo_zenith_transparente.png",
            subsample=6,
            pad = (0,10),        
            background_color="#0F2A44"
        )
    ],
    [
        sg.Text(
           "ZENITH SAÚDE",
            font=("Helvetica", 18, "bold"),
            text_color="#2C7BE5",
            background_color="#0F2A44"
        )
    ],

    [sg.Text("Utilizador:", text_color="#FFFFFF", background_color="#0F2A44"),
     sg.Input(key="-U-", size=(20,1), border_width=1, background_color="#1F4B6E", text_color="#EAF6F6")],

    [sg.Text("Password:", text_color="#FFFFFF", background_color="#0F2A44"),
     sg.Input(key="-P-", password_char="*", size=(20,1), border_width=1, background_color="#1F4B6E", text_color="#EAF6F6")],
    
    [sg.HorizontalSeparator(color="#A8BFEC", pad=(0,10))],
    [sg.Button("Entrar", size=(10,1)),
     sg.Button("Sair", size=(10,1))],

]

w_login = sg.Window("Login", layout_login, element_justification="c")

login_ativo = True
autenticado = False

while login_ativo:
    evento, valores = w_login.read()

    if evento in (sg.WIN_CLOSED, "Sair"):
        autenticado = False
        login_ativo = False

    elif evento == "Entrar":
        valido = False
        i = 0

        while i < len(users) and not valido:
            if (
                str(users[i]["id"]) == str(valores["-U-"]) and
                str(users[i]["password"]) == str(valores["-P-"])
            ):
                valido = True
            i += 1

        if valido:
            autenticado = True
            login_ativo = False
        else:
            w_login["-MSG-"].update("Credenciais inválidas!")

w_login.close()

if not autenticado:
    sg.popup("Aplicação encerrada. Até à próxima!", background_color="#0F2A44")
    exit()


# Layout Principal

menu_lateral = sg.Column(
    [
        [sg.Button("1 - Configurar Simulação", size=(26, 2), font=("Arial", 11), key="1")],
        [sg.Button("2 - Executar Simulação", size=(26, 2), font=("Arial", 11), key="2")],
        [sg.Button("3 - Limpar Resultados", size=(26, 2), font=("Arial", 11), key="3")],
        [sg.Button("4 - Histórico da Fila", size=(26, 2), font=("Arial", 11), key="4")],
        [sg.Button("5 - Relatório Global", size=(26, 2), font=("Arial", 11), key="5")],
        [sg.Button("6 - Estatísticas", size=(26, 2), font=("Arial", 11), key="6")],
        [sg.Button("7 - Pesquisar Doente", size=(26, 2), font=("Arial", 11), key="7")],
        [sg.Button("8 - Ajuda", size=(26, 2), font=("Arial", 11), key="8")],
        [
            sg.Button(
                "0 - Sair",
                expand_x=True,
                size=(26,2),
                button_color=("white", "#F53C3C")
            )
        ]
    ],
    background_color="#1E3A5F",
    pad=(15,15) 
)

conteudo = sg.Column(
    [
        [
            sg.Image(
                "logo_zenith_transparente.png",
                subsample=6,
                background_color="#8FAFC4",
                pad=((5,10),(5,5))
            ),
            sg.Text(
                "Zenith Saúde",
                font=("Helvetica", 26, "bold"),
                text_color="#0F2A44",
                background_color="#8FAFC4",
                pad=((10,0),(20,0))
            )
        ],

        [
            sg.HorizontalSeparator(color="#6E8FA8")
        ],

        [
            sg.Multiline(
                key="-OUTPUT-",
                disabled=True,
                expand_x=True,
                expand_y=True,
                font=("Consolas", 15),
                background_color="#EDF2F6",
                text_color="#0F2A44",
                border_width=1
            )
        ]
    ],
    background_color="#8FAFC4",
    expand_x=True,
    expand_y=True,
    pad=(10,10)
)


layout = [
    [menu_lateral,sg.VSeparator(color="#C6D2DC"), conteudo]
]

window = sg.Window(
    "Zenith Saúde",
    layout,
    resizable=True,
    finalize=True,
    size=(1300,750),
    return_keyboard_events=True
)

def mostrar_pessoas_na_fila(historico, doentes):

    texto = "PESSOAS NA FILA DE ESPERA\n"
    texto += "==========================\n\n"

    for tempo, fila in historico:
        if fila:
            texto += f"\n t = {tempo:6.2f} min\n"
            for did in fila:
                d = doentes[did]
                texto += (
                    f"  • {d.nome} ({did}) | "
                    f"{d.especialidade} | "
                    f"Prioridade: {d.prioridade}\n"
                )

    sg.popup_scrolled(
        texto,
        title="Doentes na Fila",
        size=(80, 30)
    )


def janela_historico_fila(resultados):

    layout = [
        [sg.Text("Histórico da Fila", font=("Helvetica", 16, "bold"), background_color="#0F2A44")],
        [sg.Text("", size=(1,1), background_color="#0F2A44")],

        [sg.Button("Tamanho da fila ao longo do tempo", size=(32,2))],
        [sg.Button("Pessoas na fila de espera", size=(32,2))],
        [sg.Text("", size=(1,1), background_color="#0F2A44")],

        [sg.HorizontalSeparator(color="#E5E7EB", pad=(0,10))],
        [sg.Button(("Fechar"), size=(12,1))]
    ]

    win = sg.Window(
        "Histórico da Fila",
        layout,
        modal=True,
        size=(420, 250),
        element_justification="c",
        resizable=False
    )

    ativa = True

    while ativa:
        evento, valores = win.read()

        if evento in (sg.WIN_CLOSED, "Fechar"):
            ativa = False

        elif evento == "Tamanho da fila ao longo do tempo":
            mostrar_historico_fila_texto(
                resultados["historico_fila_detalhado"]
            )

        elif evento == "Pessoas na fila de espera":
            mostrar_pessoas_na_fila(
                resultados["historico_fila_detalhado"],
                resultados["doentes"]
            )

    win.close()


def mostrar_historico_fila_texto(historico):

    texto = "HISTÓRICO DA FILA (Tempo → Tamanho)\n"
    texto += "====================================\n\n"

    ultimo = None
    for tempo, fila in historico:
        tamanho = len(fila)
        if tamanho != ultimo:
            texto += f"t = {tempo:6.2f} min | fila = {tamanho}\n"
            ultimo = tamanho

    sg.popup_scrolled(
        texto,
        title="Histórico da Fila",
        size=(60, 25)
    )


def janela_estatisticas(resultados):
    layout_stats = [
        [sg.Text("Estatísticas da Simulação", font=("Helvetica", 16, "bold"), background_color="#0F2A44")],
        [sg.Text("", size=(1,1), background_color="#0F2A44")],

        [sg.Button("Evolução da fila", size=(35, 2))],
        [sg.Button("Ocupação dos médicos", size=(35, 2))],
        [sg.Button("Tempo médio de espera por prioridade", size=(35, 2))],
        [sg.Button("Desistências ao longo do tempo", size=(35, 2))],
        [sg.Button("Fila média vs Taxa de chegada", size=(35, 2))],
        [sg.Button("Ocupação dos médicos ao longo do tempo", size=(35, 2))],

        [sg.HorizontalSeparator(color="#E5E7EB", pad=(0,10))],
        [sg.Button("Fechar")]
    ]

    win = sg.Window(
        "Estatísticas",
        layout_stats,
        modal=True,
        size=(420, 420),      
        element_justification="c"
    )

    estat=True

    while estat:
        evento, values = win.read()

        if evento in (sg.WIN_CLOSED, "Fechar"):
            estat=False

        elif evento == "Evolução da fila":
            grafico_evolucao_fila(resultados["historico_fila"])

        elif evento == "Ocupação dos médicos":
            grafico_ocupacao_medicos(resultados["medicos"])

        elif evento == "Tempo médio de espera por prioridade":
            grafico_tempo_medio_espera_prioridade(resultados["tempos_espera_prioridade"])

        elif evento == "Desistências ao longo do tempo":
            grafico_desistencias_tempo(resultados["historico_desistencias"])

        elif evento == "Fila média vs Taxa de chegada":
            lambdas = [10, 15, 20, 25, 30]
            grafico_fila_media_vs_lambda(lambdas)

        elif evento == "Ocupação dos médicos ao longo do tempo":
            grafico_ocupacao_ao_longo_do_tempo(resultados["historico_ocupacao"])

    win.close()


def janela_pesquisa_doente(estado_doentes):
    layout = [
        [sg.Text("Pesquisa doente:", font=("Helvetica", 14, "bold"), background_color="#0F2A44")],
        [sg.Text("ID do Doente:", background_color="#0F2A44")],
        [sg.Input(key="-ID-DOENTE-", size=(10,1), background_color="#0F2A44"), sg.Button("Pesquisar")],
        [sg.Multiline(size=(50,10), key="-RESULTADO-", disabled=True)],
        [sg.Button("Fechar")]
    ]

    win = sg.Window("Pesquisa de Doente", layout, modal=True)

    ativa = True

    while ativa:
        evento, valores = win.read()

        if evento in (sg.WIN_CLOSED, "Fechar"):
            ativa = False

        elif evento == "Pesquisar":
            did = valores.get("-ID-DOENTE-", "").strip()

            if did:
                if did in estado_doentes:
                    d = estado_doentes[did]

                    texto = (
                        f"Doente ID: {did}\n"
                        f"Estado: {d.get('estado', '—')}\n"
                        f"Chegada: {d.get('chegada', '—')}\n"
                        f"Início consulta: {d.get('inicio', '—')}\n"
                        f"Saída: {d.get('saida', '—')}"
                    )
                else:
                    texto = "Doente não encontrado."
            else:
                texto = "Introduza um ID."

            win["-RESULTADO-"].update(texto)

    win.close()


# Variáveis de estado

executar = True
resultados = None

# Janela de Configurações

def janela_configuracoes():
    global NUM_MEDICOS, TEMPO_SIMULACAO, TAXA_CHEGADA, DISTRIBUICAO_TEMPO_CONSULTA

    layout_conf = [
        [sg.Text("Configurar Simulação", font=("Helvetica", 16, "bold"), background_color="#0F2A44")],

        [sg.Text("Número de médicos", background_color="#0F2A44"),
         sg.Slider(
             range=(1, 10),
             default_value=NUM_MEDICOS,
             orientation="h",
             size=(30, 15),
             key="-MEDICOS-",
             enable_events=True
         ),
         sg.Text(str(NUM_MEDICOS), size=(4,1), key="-MEDICOS-VAL-", background_color="#0F2A44")],

        [sg.Text("Tempo de simulação (horas)", background_color="#0F2A44"),
         sg.Slider(
             range=(1, 12),
             default_value=TEMPO_SIMULACAO // 60,
             orientation="h",
             size=(30, 15),
             key="-TEMPO-",
             enable_events=True
         ),
         sg.Text(str(TEMPO_SIMULACAO // 60), size=(4,1), key="-TEMPO-VAL-", background_color="#0F2A44")],

        [sg.Text("Taxa de chegada (doentes/hora)", background_color="#0F2A44"),
         sg.Slider(
             range=(5, 40),
             default_value=int(TAXA_CHEGADA * 60),
             orientation="h",
             size=(30, 15),
             key="-CHEGADA-",
             enable_events=True
         ),
         sg.Text(str(int(TAXA_CHEGADA * 60)), size=(4,1), key="-CHEGADA-VAL-", background_color="#0F2A44")],

        [sg.Text("Distribuição do tempo de consulta", background_color="#0F2A44"),
         sg.Combo(
             ["exponential", "normal", "uniform"],
             default_value=DISTRIBUICAO_TEMPO_CONSULTA,
             key="-DIST-",
             readonly=True
         )],

        [sg.HorizontalSeparator()],
        [sg.Button("Guardar"), sg.Button("Fechar")]
    ]

    win = sg.Window("Configurações", layout_conf, modal=True)

    ativa = True
    guardar = False

    while ativa:
        event, values = win.read()

        if event == "-MEDICOS-":
            win["-MEDICOS-VAL-"].update(int(values["-MEDICOS-"]))

        elif event == "-TEMPO-":
            win["-TEMPO-VAL-"].update(int(values["-TEMPO-"]))

        elif event == "-CHEGADA-":
            win["-CHEGADA-VAL-"].update(int(values["-CHEGADA-"]))

        elif event == "Guardar":
            guardar = True
            ativa = False   

        elif event in (sg.WIN_CLOSED, "Fechar"):
            guardar = False
            ativa = False   

    if guardar:
        NUM_MEDICOS = int(values["-MEDICOS-"])
        TEMPO_SIMULACAO = int(values["-TEMPO-"]) * 60
        TAXA_CHEGADA = int(values["-CHEGADA-"]) / 60
        DISTRIBUICAO_TEMPO_CONSULTA = values["-DIST-"]

    win.close()
    return guardar


# Loop Principal

while executar:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == "0 - Sair":
        executar = False

    elif event == "0":
        executar = False

    elif event == "1":
        guardou = janela_configuracoes()
        if guardou:
            window["-OUTPUT-"].update("✔ Configurações atualizadas.\n")

    elif event == "2":
        resultados = simula()

        window["-OUTPUT-"].update(
            "✔ Simulação executada com sucesso\n\n"
            f"Número de médicos: {NUM_MEDICOS}\n"
            f"Tempo de simulação: {TEMPO_SIMULACAO / 60:.1f} horas\n"
            f"Taxa de chegada: {TAXA_CHEGADA * 60:.1f} doentes/hora\n"
            f"Tamanho médio da fila: {resultados['fila_media']:.2f}\n"
        )

    elif event == "3":
        window["-OUTPUT-"].update("")

    elif event == "4":
        if resultados is None:
            window["-OUTPUT-"].update("⚠ Execute a simulação primeiro.\n")
        else:
            janela_historico_fila(resultados)


    elif event == "5":
        if resultados is None:
            window["-OUTPUT-"].update("⚠ Execute a simulação primeiro.\n")
        else:
            texto = (
                " RELATÓRIO GLOBAL DA SIMULAÇÃO\n"
                "================================\n\n"
                f" Número de médicos: {NUM_MEDICOS}\n"
                f" Doentes atendidos: {resultados['doentes_atendidos']}\n"
                f" Doentes que desistiram: {resultados['desistencias']}\n\n"
                f" Tempo médio de espera: {resultados['media_espera']:.2f} min\n"
                f" Tempo médio na clínica: {resultados['media_sistema']:.2f} min\n\n"
                f" Tamanho médio da fila: {resultados['fila_media']:.2f}\n"
                f" Tamanho máximo da fila: {resultados['fila_max']}\n\n"
                " Ocupação dos Médicos:\n"
            )

            for m in resultados["medicos"]:
                ocup = (m.total_tempo_ocupado / TEMPO_SIMULACAO) * 100
                texto += f"   • Médico {m.id} ({m.especialidade}): {ocup:.1f}%\n"

            window["-OUTPUT-"].update(texto)

    elif event == "6":
        if resultados is None:
            window["-OUTPUT-"].update("Execute a simulação primeiro.\n")
        else:
            janela_estatisticas(resultados)


    elif event == "7":
        if resultados is None:
            window["-OUTPUT-"].update("Execute a simulação primeiro.\n")
        else:
            janela_pesquisa_doente(resultados["estado_doentes"])
        
    elif event == "8":
        sg.popup_scrolled(
            " Ajuda",
            " =========================\n\n"

            " 1 - Configurar Simulação\n"
            "  Permite alterar os principais parâmetros da simulação:\n"
            "   • Número de médicos disponíveis\n"
            "   • Duração total da simulação (em horas)\n"
            "   • Taxa de chegada de doentes (doentes por hora)\n"
            "   • Distribuição estatística do tempo de consulta\n\n"

            " 2 - Executar Simulação\n"
            "  Inicia a simulação com os parâmetros atualmente definidos.\n\n"

            " 3 - Limpar Resultados\n"
            "  Limpa a área de saída da interface gráfica.\n"
            "  Não altera parâmetros nem apaga resultados internos.\n\n"

            " 4 - Histórico da Fila\n"
            "  Apresenta informação detalhada sobre a evolução da fila de espera ao\n" 
            "  longo da simulação.\n"
            "  Permite consultar:\n"
            "   • A variação do tamanho da fila ao longo do tempo\n"
            "   • A lista de doentes que estiveram na fila de espera ao longo do tempo, com a respetiva prioridade e especialidade\n\n"

            " 5 - Relatório Global da Simulação\n"
            "  Apresenta um resumo completo da simulação executada,\n"
            "  incluindo:\n"
            "   • Número de médicos\n"
            "   • Doentes atendidos e desistências\n"
            "   • Tempos médios de espera e permanência\n"
            "   • Tamanho médio e máximo da fila\n"
            "   • Ocupação percentual de cada médico\n\n"

            " 6 - Estatísticas\n"
            "  Gera gráficos estatísticos da simulação, nomeadamente:\n"
            "   • Evolução do tamanho da fila ao longo do tempo\n"
            "   • Ocupação dos médicos\n"
            "   • Tempo médio de espera por prioridade\n"
            "   • Número de desistências ao longo do tempo\n"
            "   • Tamanho médio da fila vs Taxa de chegada (λ)\n\n"

            " 7 - Pesquisar Doente\n"
            "  Permite pesquisar um doente específico através do seu ID (p__ ).\n"
            "  Apresenta informação individual sobre o percurso do doente na\n"
            "  simulação, incluindo:\n"
            "   • Estado atual (em espera, em consulta, atendido ou desistiu)\n"
            "   • Tempo de chegada\n"
            "   • Início da consulta (se aplicável)\n"
            "   • Momento de saída do sistema\n\n"

            " 0 - Sair\n"
            "  Encerra a aplicação de forma segura.\n"
        )
        
window.close()