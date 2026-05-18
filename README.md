<p align="center">
  <img src="static/assets/img/MORSy-CI.png" width="250" alt="MORsy-CI Logo">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version">
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3"></a>
</p>

**MORsy-CI** (*Multi-Objective Robust System for Constructing Composite Indicators*) é uma plataforma científica de vanguarda projetada para a construção de indicadores compostos. É o primeiro sistema a integrar otimização multi-objetivo com critérios rigorosos de qualidade, preenchendo lacunas críticas de subjetividade e arbitrariedade presentes em métodos tradicionais.

Ao harmonizar objetivos conflitantes, o MORsy-CI garante robustez técnica sem sacrificar a interpretabilidade, oferecendo uma estrutura transparente para a análise de políticas públicas e desigualdades urbanas.

---

## 🧠 Inovação Metodológica

Diferente de softwares limitados a métodos isolados, o MORsy-CI utiliza **busca não-local (non-local search)** para maximizar simultaneamente quatro pilares de confiabilidade:

1.  **Poder Explicativo (Explanatory power):** Maximiza a relação com variáveis de referência.
2.  **Poder Informacional (Informational power):** Retém o máximo de informação das variáveis subjacentes.
3.  **Poder Discriminante (Discriminating power):** Garante a diferenciação clara entre as unidades analisadas.
4.  **Estabilidade:** Minimiza a incerteza e garante medições confiáveis.

Essa abordagem supera limitações comuns, como a sensibilidade a *outliers* e vieses de agregação compensatória, resultando em indicadores que excedem os limiares de referência da literatura científica.

---

## 🌟 Principais Recursos

- **Ponderação Otimizada:** Algoritmo que elimina a atribuição arbitrária de pesos através de critérios objetivos de qualidade.
- **Normalização e Tratamento de Dados:** Suporte a métodos *Robust*, *Normal* e *Ranking*, com remoção automática de outliers para garantir a integridade da análise.
- **Processamento Paralelo:** Motor de cálculo de alto desempenho para processamento simultâneo de múltiplos indicadores.
- **Benchmarking Comparativo:** O sistema gera automaticamente resultados via métodos clássicos para validação:
    - **PCA:** Foco em retenção de informação original.
    - **BoD (Benefit of the Doubt):** Foco em evitar disputas políticas de pesos.
    - **Entropy:** Foco em facilitar a interpretação dos resultados.
    - **Equal Weights:** Foco na simplicidade de comunicação.
- **Dashboards de Decisão:** Visualizações avançadas para reduzir o estresse cognitivo do tomador de decisão:
    - Histogramas e Gráficos de Dispersão.
    - Mapas de calor de correlação.
    - Gráficos de categorias paralelas para análise de sensibilidade e incerteza.

---

## 📊 Estudo de Caso

O sistema foi validado com dados da cidade de **São Sebastião do Paraíso (MG)**, onde revelou com precisão padrões centro-periferia na oferta de serviços públicos (saneamento, pavimentação, iluminação). 

**Resultado:** O MORsy-CI superou métodos tradicionais (PCA, BoD, Entropia) em pelo menos três das quatro dimensões avaliadas, provando ser uma ferramenta prática e replicável para promover a equidade territorial.

---

## 🚀 Roadmap e Futuro

O MORsy-CI é um projeto em constante evolução. Nossos próximos passos incluem:
- **Limiares Flexíveis:** Permitir a configuração personalizada de rigor para as medidas de confiabilidade.
- **Opinião de Especialistas:** Integrar restrições de pesos mínimos e máximos baseados em conhecimento especializado.
- **Novas Técnicas de Agregação:** Incluir diferentes abordagens de normalização e agregação de sub-indicadores.
- **Análise de Sensibilidade Expandida:** Considerar múltiplas variáveis de ligação e novos indicadores de medições atípicas.

---

## 📄 Publicação

Este software é o resultado de uma pesquisa científica detalhada. Se você utilizar o MORsy-CI em seu trabalho, por favor, cite nosso artigo original (link em breve).

---

## 🔗 Demo ao Vivo

Acesse a aplicação em produção aqui:  
👉 [MORsy-CI Live](https://robust-optimizer-1033542820153.southamerica-east1.run.app/)

---

## 🛠️ Stack Tecnológica

- **Backend:** Python com Flask
- **Processamento de Dados:** Pandas, NumPy
- **Visualização:** Plotly
- **Infraestrutura:** Google Cloud Run, Firestore, Storage

---

## 🚀 Começando

### Pré-requisitos

- Python 3.9+
- Google Cloud SDK configurado.

### Instalação Local

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/robust-optimizer.git
   cd robust-optimizer
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o servidor de desenvolvimento:**
   ```bash
   python main.py
   ```

---

## ☁️ Deploy no Google Cloud

Para realizar o build e deploy na infraestrutura gerenciada:

```bash
# Via Cloud Build
gcloud builds submit --tag gcr.io/robust-optimizer/index 
gcloud run deploy --image gcr.io/robust-optimizer/index --platform managed

# Ou diretamente via código fonte
gcloud run deploy --source .
```

---

## 📂 Estrutura do Projeto

- `main.py`: Aplicação web principal, gestão de rotas e interface com o usuário.
- `processardados.py`: Motor de processamento paralelo e lógica de otimização.
- `static/`: Recursos estáticos (CSS, JS, imagens).
- `templates/`: Templates Jinja2 para renderização HTML.

---

## 📄 Licença

Distribuído sob a licença GNU GPL v3.0. Consulte o arquivo `LICENSE` para obter mais informações.





### Versão Anterior

- robust-optimizer
Otimizador Robusto Multi Objetivo

- Cloud buid & deploy
gcloud buids submit --tag gcr.io/robust-optimizer/index 
gcloud run deploy --image gcr.io/robust-optimizer/index --platform managed


- Ou apenas
gcloud run deploy --source . --set-env-vars FLASK_SECRET_KEY="sua_chave_secreta_aqui" CLOUD_STORAGE_BUCKET="nome_do_seu_bucket"



- To revert update
gcloud components update --version 508.0.0
