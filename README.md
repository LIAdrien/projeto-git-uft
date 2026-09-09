# projeto-git-uft
Projeto Integrador - Estrutura inicial, mapeamento de requisitos e documentação do projeto.

# Projeto Integrador - Sprint 1

## Descrição do Projeto
[Insira aqui uma breve descrição do que o seu sistema/aplicativo fará].

---

## 1. Identificação da Equipe e Links

| Nome do Integrante | Usuário GitHub (@) | Papel Principal no Time |
| :--- | :--- | :--- |
| Laura Nicolle Anjos de Lima | @LIAdrien | Product Owner (PO) |
| [Nome Completo 2] | @ | Scrum Master (SM) |
| Matheus Felipe dos Santos Pereira | Matheu4felipe | Desenvolvedor / Equipe Técnica |
| Davi Pereira Borges | @pereiradavi-creator | Desenvolvedor / Equipe Técnica |
| [Nome Completo 5] | @ | Desenvolvedor / Equipe Técnica |

* **Link do Repositório GitHub:** https://github.com/usuario/nome-do-repositorio

---

## 2. Fundamentação e Dinâmica dos Papéis Ágeis

### A) Product Owner (PO)
1. **Quem é o Product Owner da equipe?**
   * Laura Nicolle Anjos de Lima
2. **Quais são as principais atribuições e responsabilidades do PO perante o Projeto Integrador?**
   * Domínio do negócio e priorização do backlog
3. **Como o PO validará se as funcionalidades entregues realmente cumprem o propósito do projeto?**
   * Avaliar e comparar as funcionalidades preenchem os requisitos do projeto

### B) Scrum Master (SM)
1. **Quem é o Scrum Master da equipe?**
   * [Nome do integrante]
2. **Quais são as responsabilidades do Scrum Master na condução do time?**
   * Remoção de impedimentos, facilitação das reuniões, garantia da metodologia Scrum
3. **Qual será o canal de comunicação oficial da equipe e a frequência dos alinhamentos semanais?**
   * WhatsApp, Discord e encontros após as aulas

---

## 3. Especificação de Requisitos Funcionais (RF)

| ID | Nome do Requisito | Descrição / História de Usuário | Critérios de Aceite (Validação) |
| :--- | :--- | :--- | :--- |
| **RF01** | Autenticação do Cidadão | Como cidadão, quero fazer login seguro (ex: Gov.br ou gov-local), para garantir que apenas eu veja meus dados. | 1. Credenciais inválidas devem retornar erro. 2. Acesso aos dados bloqueado sem login. |
| **RF02** | Consulta de Débitos | Como cidadão autenticado, quero consultar meus débitos pendentes, para emitir a guia de pagamento. | 1. Exibir tabela com dívidas ativas. 2. Mostrar valor total e data de vencimento. |
| **RF03** | Emissão de Guia | Como cidadão, quero gerar a guia de pagamento em PDF, para efetuar o pagamento online ou no banco. | 1. Gerar PDF com código de barras/PIX. 2. PDF deve conter dados da prefeitura. |
| **RF04** | Filtro de IPTU Social | Como analista da SEFIN, quero filtrar a base de contribuintes por faixa de renda, para identificar beneficiários do IPTU Social. | 1. Permitir filtro por valor de renda. 2. Listar apenas resultados compatíveis. |
| **RF05** | Exclusão Automática | Como analista, quero excluir automaticamente da cobrança os beneficiários do IPTU Social, para cumprir a lei de isenção. | 1. Atualizar status para "Isento". 2. Impedir emissão de cobrança para estes CPFs. |
| **RF06** | Exportação de Ranking | Como analista, quero exportar o ranking de recuperação de dívida ativa em PDF, para instruir processos administrativos. | 1. PDF deve listar os maiores devedores recuperados. 2. Conter data e hora da geração. |
| **RF07** | Relatório de Arrecadação | Como secretário, quero visualizar o relatório de arrecadação de IPTU/ISS consolidado do mês, para acompanhar as metas. | 1. Gráfico ou tabela totalizadora. 2. Filtro por mês/ano. |
| **RF08** | Auditoria de Acessos | Como administrador, quero que o sistema registre logs de acesso, para auditoria em caso de vazamento. | 1. Gravar IP, Usuário, Data e Ação no banco de dados invisível ao usuário comum. |
| **RF09** | Exportação de Dados em CSV | Como analista, quero exportar dados da tabela de devedores em formato CSV, para cruzamento de dados em outras planilhas. | 1. O arquivo CSV deve ser delimitado por ponto e vírgula. 2. O download deve iniciar imediatamente. |
| **RF10** | Cadastro de Servidores | Como administrador, quero cadastrar os analistas e secretários no sistema, definindo níveis de acesso. | 1. Usuário Secretário só vê relatórios. 2. Analista tem acesso aos processos de dívida. |

---

## 4. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição da Restrição | Métrica / Forma de Teste |
| :--- | :--- | :--- | :--- |
| **RNF01** | Privacidade (LGPD) | O sistema deve esconder ou criptografar os dados sensíveis (nome, CPF, endereço) e exigir conexão segura (HTTPS). | Tentativa de acesso sem autenticação deve redirecionar para a tela de Login. |
| **RNF02** | Desempenho | O sistema precisa responder às consultas do cidadão no banco de dados de forma ágil. | Tempo de resposta para consultas não deve ultrapassar 3 segundos em 95% dos casos. |
| **RNF03** | Tecnologia / Backend | O sistema deve ser desenvolvido obrigatoriamente utilizando a linguagem Python. | O código deve ser executável em ambiente Python 3.12+. |
| **RNF04** | Portabilidade | As dependências do projeto devem estar isoladas e descritas em arquivo de manifesto. | A instalação deve ser bem-sucedida usando o comando `pip install -r requirements.txt`. |

---

## 5. Matriz de Priorização MoSCOW

*   **Must Have (Indispensável para o MVP):** RF01 (Autenticação), RF02 (Consulta), RF04 (Filtro IPTU Social), RF05 (Exclusão Automática), RNF01 (Privacidade), RNF03 (Python). 
*   **Should Have (Importante, alta prioridade):** RF03 (Emissão de Guia), RF07 (Relatório de Arrecadação), RF10 (Cadastro de Servidores), RNF02 (Desempenho).
*   **Could Have (Desejável):** RF06 (Exportação de Ranking em PDF), RF09 (Exportação CSV), RNF04 (Portabilidade).
*   **Won't Have (Fora do escopo desta entrega inicial):** RF08 (Auditoria de Acessos).

---
