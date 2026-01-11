# Sistema de Simulação de Clínica Médica (ZenithSaúde)

Um sistema desenvolvido em Python para gestão e análise de simulações clínicas. O sistema disponibiliza uma **Interface Gráfica (FreeSimpleGUI)** simples e intuitiva.

## Requisitos

- Python 3.7 ou superior

## Instalação

1. Criar um ambiente conda com Python 3.12:
```bash
conda create -n clinic_sim python=3.12
conda activate clinic_sim

2. Instalar os pacotes necessários:
```bash
pip install numpy matplotlib FreeSimpleGUI
```

## Correr a aplicação

-Para carregar o sistema clinico é necessário:

python ZenithSaúde.py

## Simulação de parâmetros

NUM_MEDICOS = 3           

TAXA_CHEGADA = 10 / 60    # 10 doentes por h -> para min

TEMPO_MEDIO_CONSULTA = 15 

TEMPO_SIMULACAO = 8 * 60  # aprox 8h

DISTRIBUICAO_TEMPO_CONSULTA = "exponential"; "normal"; "uniforme" 

ESPECIALIDADES = ["cardiologia", "ortopedia", "neurologia"]

PRIORIDADES = {"vermelho": 0, "amarelo": 1, "verde": 2} # menor número = maior prioridade

CHEGADA = "chegada"

SAIDA = "saída"

DESISTENCIA = "desistência"

TEMPO_MAX_ESPERA = {"vermelho": float("inf"), "amarelo": 60, "verde": 30}


## Funcionalidades

-Configurar Simulação

-Executar Simulação

-Limpar Resultados

-Histórico da Fila

-Relatório Global da Simulação

-Estatísticas

-Pesquisar Doente

-Ajuda

-Sair

## Interface Gráfica (GUI)

A interface gráfica do sistema oferece uma navegação intuitiva através de vários separadores, permitindo configurar, executar e analisar a simulação de forma eficiente.

### Funcionalidades da Interface

- **Configurar Simulação**
  - Definir os parâmetros da simulação
  - Ajustar taxas de chegada
  - Selecionar o modelo de distribuição estatística

- **Executar Simulação**
  - Iniciar o motor de simulação
  - Registar eventos em tempo real
  - Processamento dos atendimentos

- **Limpar Resultados**
  - Repor o sistema
  - Limpar a área de saída e resultados anteriores

- **Histórico da Fila**
  - Visualizar registos textuais da fila
  - Consultar detalhes e histórico de espera dos pacientes

- **Relatório Global da Simulação**
  - Apresentar indicadores-chave de desempenho
  - Analisar a eficiência e ocupação médica

- **Pesquisar Doente**
  - Funcionalidade de pesquisa de registos

- **Estatísticas**
  - Evolução da fila ao longo do tempo
  - Ocupação dos médicos durante a simulação
  - Tempo médio de espera por prioridade
  - Acumulação de desistências
  - Taxa mádia da fila vs Taxa de Chegada
  - Ocupação médicos ao longo do tempo

- **Ajuda**
  - Explicação das funcionalidades da aplicação
  - Descrição dos parâmetros da simulação

- **Sair**
  - Encerramento seguro da aplicação e da interface gráfica


## Base de Dados

O nosso sistema usa .json para armazenar a base de dados:

- Dataset Pacientes: pessoas.json 
- Credencias doentes: users.json

## Tratamento de Erros

O sistema inclui mecanismos de tratamento de erros:

-Validação de entradas

-Restrições de valores

-Alertas de estado vazio


### Estrutura Projeto:

ZenithSaude/
├── ZenithSaúde.py                      # Aplicação principal, GUI e motor de simulação
├── data/
│   ├── pessoas.json                    # Dataset para geração de perfis de pacientes
│   └── users.json                      # Credenciais encriptadas para o sistema de login
├── assets/
│   └── logo_zenith_transparente.png    # Recursos gráficos da interface
└── README.md                           # Documentação do projeto

## Análise dos Resultados:

-Impacto da Taxa de Chegada (λ):

Verificou-se que o tamanho médio da fila aumenta com o crescimento da taxa de chegada de pacientes. Para valores elevados de λ, o sistema entra rapidamente em saturação, ultrapassando a capacidade da clínica.

-Eficiência da Triagem de Manchester:

O sistema de prioridades (Vermelho, Amarelo e Verde) assegura tempos de espera significativamente menores para casos urgentes. Os gráficos de Tempo de Espera por Prioridade demonstram claramente esta diferenciação.

-Ocupação Médica:

A análise da ocupação revelou possíveis problemas de gestão de recursos. Valores próximos de 100% indicam risco de sobrecarga e exaustão médica, enquanto valores baixos sugerem excesso de profissionais.

-Mecanismo de Desistência:

O gráfico de desistências acumuladas evidencia a perda de pacientes em períodos de elevado congestionamento, sendo um indicador crítico da qualidade do serviço e estabilidade do sistema.