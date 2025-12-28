Scraper do site da CBX, FIDE, ChessResults, USCF e sua federação!

Todos os dados Brutos são enviados ao SupaBase DB Bronze
Depois eu baixo de volta, faço um tratamento manual
Passo por um tratamento programático, com os tipos corretos, ISO, bem padronizado
E envio para o SupaBase novamente como DB Ouro

Comando para executar todos os testes:
`export PYTHONPATH=$PYTHONPATH:$(pwd)/src && pytest` ou `$env:PYTHONPATH = "src"; pytest`

---

> https://ratings.fide.com/tournament_information.phtml?event=34900 > https://ratings.fide.com/report.phtml?event=15066

```json
{
  "CHESSRESULTS": {
    "torneios": "ScraperChessresultsTorneios",
    "country": "AFG"
  }
}
```
2025-12-23 21:26:09,141 - INFO - [ScraperChessresultsTorneios] - Lote 1327201-1327300: Nenhum torneio encontrado.
---


Todos os scrapers devem ser ASYNC! Ou majoritariamente ASYNC