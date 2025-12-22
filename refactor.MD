# Documentação do Sistema de Web Scraping

## Visão Geral

Sistema modular de web scraping projetado para extrair dados de múltiplas fontes (CBX, FIDE, USCF, ...) e persistir em camadas Bronze no Supabase. O sistema é organizado em uma hierarquia de três níveis (Provedor, Entidade e Argumentos) para garantir escalabilidade e manutenção isolada.

## Estrutura de Arquivos

A organização segue a separação por domínio de site para reaproveitamento de sessões e headers específicos.

```text
/scrapers
├── base_scraper.py         # Classe abstrata com lógica global (logs, persistência)
├── dispatcher.py           # Orquestrador que recebe o JSON da API e inicia os processos
├── cbx/
│   ├── base_cbx.py         # Lógica compartilhada do site (ASP.NET vars, session)
│   ├── comunicados.py      # Extração específica de comunicados
│   └── torneios.py         # Extração específica de torneios
├── fide/
│   ├── base_fide.py        # Lógica de headers e bypass de proteção FIDE
│   └── jogadores.py        # Extração específica de perfis de jogadores
└── utils/
    ├── database.py         # Funções de upsert para o Supabase
    └── network.py          # Rotação de User-Agents e proxies
```

## Arquitetura de Classes

O sistema utiliza herança múltipla para especializar os scrapers:

1. **Scraper (Classe Base):** Contém os métodos globais de salvamento e tratamento de erros comuns.
2. **ScraperSite (Classe Intermediária):** Implementa as peculiaridades de rede de cada provedor (ex: `ScraperCbx` lida com o estado da sessão ASP.NET).
3. **ScraperEntity (Classe Final):** Contém apenas seletores CSS/XPath e lógica de parsing (ex: `ScraperCbxTournaments`).

## Protocolo de Comunicação (API)

O serviço aceita um objeto JSON hierárquico. A rota única no Render processa o payload e despacha as tarefas para os respectivos módulos.

### Formato do Payload

```json
{
   "CBX": {
      "max_pages": "10",
      "torneios": {
         "year": "2024",
         "month": "11"
      },
      "jogadores": {
         "state": "SP"
      }
   },
   "FIDE": {
      "torneios": {
         "country": "*",
         "period": "2024-11-01"
      }
   }
}

```

## Fluxo de Execução

1. O Supabase Cron realiza uma requisição HTTP POST para o serviço no Render.
2. O `dispatcher.py` analisa as chaves de primeiro nível (Provedores).
3. As classes de cada provedor são instanciadas passando os argumentos globais e específicos.
4. Cada scraper executa seu ciclo de extração e realiza o `upsert` diretamente no Supabase.
5. Falhas em um scraper específico não interrompem a execução de outros provedores no mesmo payload.
