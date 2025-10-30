# 🌌 Detecção de Eventos Astronômicos em Imagens com MapReduce

## 📘 Descrição Geral do Projeto

Este projeto tem como objetivo desenvolver um sistema de **detecção automática de eventos astronômicos transitórios** (como supernovas, estrelas variáveis e asteroides) através da **análise de imagens astronômicas obtidas em diferentes momentos**, utilizando o **paradigma de processamento distribuído MapReduce**.

O projeto faz parte de um **Trabalho de Conclusão de Curso (TCC)** e busca demonstrar como técnicas de Big Data podem ser aplicadas a grandes volumes de dados astronômicos reais, explorando a variação temporal observada nas imagens do **Zwicky Transient Facility (ZTF)**.

---

## 🧠 Conceito Fundamental

Eventos astronômicos transitórios são fenômenos que **alteram o brilho ou a posição de um objeto no céu ao longo do tempo**. Para detectá-los, é necessário comparar **imagens de uma mesma região do céu obtidas em momentos diferentes** e identificar mudanças significativas.

O método adotado é baseado na técnica chamada **Difference Imaging Analysis (DIA)**:

reference (céu estável)   →   imagem base
science (nova imagem)     →   observação atual
-------------------------------------------
difference = science - reference

O resultado (`difference`) realça apenas os pontos onde houve variação — o que permite detectar, por exemplo, o surgimento de uma supernova ou o movimento de um asteroide.

---

## 🎯 Objetivo Específico

Desenvolver um **pipeline distribuído** (utilizando **MapReduce**, com **PySpark** ou arquitetura equivalente) que:

1. **Baixe** imagens astronômicas reais (FITS) do **ZTF**;
2. **Organize** e **pré-processe** essas imagens;
3. **Compare** observações da mesma região em tempos diferentes;
4. **Detecte automaticamente** possíveis eventos transitórios;
5. **Valide** os resultados com eventos reais registrados no catálogo público do ZTF.

---

## 🌍 Base de Dados: Zwicky Transient Facility (ZTF)

O **ZTF** é um observatório automatizado operado pelo Caltech e IPAC, projetado especificamente para **varredura do céu noturno** e **detecção de eventos transitórios**.

### 🔭 Motivos da Escolha
- Alta **cadência temporal**: revisita as mesmas regiões várias vezes por noite.
- **Amplo campo de visão** (47 deg² por exposição).
- Dados **públicos e gratuitos**, com API e documentação extensa.
- Imagens **calibradas**, prontas para análise.
- Inclui **diferentes tipos de imagens (science, reference, difference)** e **catálogos de eventos reais** para validação.

---

## 📂 Estrutura dos Dados

Cada região do céu observada pelo ZTF é armazenada como uma imagem no formato **FITS**.

As principais categorias são:

| Tipo | Nome no portal | Descrição | Uso neste projeto |
|------|----------------|------------|------------------|
| **Science Image** | `sci` | Imagem nova da observação atual | Entrada principal (imagem a ser analisada) |
| **Reference Image** | `ref` | Imagem composta e estável, usada como base | Comparação para detectar variação |
| **Difference Image** | `diff` | Resultado oficial `science - reference` do ZTF | Validação dos resultados |

Essas imagens contêm cabeçalhos FITS com metadados essenciais:
- Coordenadas (RA, Dec)
- Data da observação (MJD)
- Filtro espectral (g, r, i)
- Campo, CCD e QID
- Exposição, seeing, etc.

---

## ⚙️ Arquitetura Geral do Sistema

O sistema segue uma arquitetura de **pipeline distribuído** inspirada no modelo **MapReduce**, onde cada imagem é processada de forma independente e depois combinada para gerar os resultados globais.

### 🔸 Fluxo de Dados
[Download] → [Pré-processamento] → [Map (Diferença)] → [Reduce (Detecção)] → [Validação]

### 🔹 Etapas detalhadas:

1. **Download das Imagens**
   - Consultar a API do ZTF via `astroquery` ou `requests`.
   - Filtrar imagens por coordenadas, filtro e datas.
   - Baixar as versões `sci` e `ref` correspondentes.

2. **Organização dos Dados**
   - Estruturar as pastas conforme os eventos analisados.
   - Exemplo:
     ```
     /data/
       ├── supernova_ZTF21aaoryop/
       │    ├── before/
       │    ├── after/
       │    └── diff_official/
     ```

3. **Pré-processamento**
   - Leitura FITS (`astropy.io.fits`)
   - Alinhamento astrométrico (`astropy.wcs`, `reproject`)
   - Normalização e remoção de ruído

4. **Fase Map**
   - Subtrai imagens (`science - reference`)
   - Gera mapas binários de variação

5. **Fase Reduce**
   - Consolida regiões de variação em potenciais eventos

6. **Validação**
   - Compara resultados com o catálogo ZTF/ALeRCE.

---

## 🧮 Tecnologias Utilizadas

| Categoria | Ferramentas / Bibliotecas |
|------------|---------------------------|
| **Linguagem** | Python 3.11 |
| **Distribuído** | PySpark / Hadoop MapReduce |
| **Astronomia** | astropy, astroquery, reproject |
| **Imagens** | opencv, scikit-image, numpy, matplotlib |
| **Validação** | pandas, requests |
| **Visualização** | matplotlib, seaborn, plotly |
| **Containerização** | Docker, Docker Compose |

---

## 📁 Estrutura do Projeto

```
DDTE/
├── src/                  # Código-fonte da aplicação
│   └── main.py          # Aplicação principal (Flask API)
├── data/                # Dados astronômicos (criado em runtime)
├── docker-compose.yml   # Orquestração de containers
├── Dockerfile           # Imagem Docker do Python
├── requirements.txt     # Dependências Python
├── .gitignore          # Arquivos ignorados pelo Git
├── .dockerignore       # Arquivos ignorados pelo Docker
└── README.md           # Documentação do projeto
```

---

## 🧭 Passo a Passo de Execução

### 🐳 Opção 1: Usando Docker (Recomendado)

1️⃣ **Iniciar o container**
```bash
docker-compose up -d
```

2️⃣ **Verificar logs**
```bash
docker-compose logs -f python-app
```

3️⃣ **Parar o container**
```bash
docker-compose down
```

4️⃣ **Acessar o shell do container**
```bash
docker-compose exec python-app bash
```

### 💻 Opção 2: Ambiente local (sem Docker)

1️⃣ **Configurar ambiente**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2️⃣ **Selecionar eventos reais**
Buscar coordenadas e datas no catálogo ALeRCE/TNS.

3️⃣ **Baixar imagens**
Usar `astroquery` e salvar em `/data/`.

4️⃣ **Executar pipeline**
Rodar fases Map e Reduce no Spark.

5️⃣ **Comparar com difference oficial**
Verificar similaridade visual e espacial.

6️⃣ **Gerar métricas**
Precision, recall, tempo médio e acurácia espacial.

---

## 📊 Possíveis Extensões Futuras
- CNN para classificação de eventos.
- Tracking de asteroides.
- Interface web de visualização.

---

## 🧾 Referências
- Bellm, E. C. et al. (2019) *ZTF: System Overview.* PASP.
- Masci, F. J. et al. (2019) *ZTF Data System.* PASP.
- Bloom, J. S. et al. (2012) *Automating Discovery and Classification of Transients.*
- IRSA ZTF Docs: https://irsa.ipac.caltech.edu/data/ZTF/docs/
- ALeRCE: https://alerce.online/

---

## 💬 Conclusão

Este projeto une **Big Data**, **Astronomia** e **Processamento Paralelo** para demonstrar que é possível aplicar conceitos de MapReduce na detecção de eventos astronômicos reais, utilizando imagens do **Zwicky Transient Facility** como base experimental.