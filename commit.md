**Related:** PR #18868

### Motivation

Lichess currently has an API for FIDE players, but not for FIDE tournaments. Adding a FIDE tournaments API would provide useful tournament data to the community.

### Proposal

Create a Lichess API endpoint that exposes FIDE tournament information, similar to the existing [FIDE players API](https://lichess.org/api#tag/fide/GET/api/fide/player/).

### FIDE API:

I've scraped the entire FIDE tournaments database from https://ratings.fide.com/rated_tournaments.phtml and discovered their internal API at `https://ratings.fide.com/a_tournaments_panel.php`.

```javascript
[
  "431621", // Tournament ID
  "XI OPEN INTERNACIONAL...", // Tournament name
  "Santa Pola (Alicante)", // City
  "s", // Type indicator
  "2025-12-20", // Start date
  "2025-12-27", // End date
  "January 2026", // Rating period
  "2026-01-01", // Rating date
  "0", // I have no idea
];
```

**Note:** The API doesn't include all tournament details (like INFORMATION or EVENT fields), but these can be accessed via:

```
https://ratings.fide.com/tournament_information.phtml?event={tournament_id}
https://ratings.fide.com/report.phtml?event={tournament_id}
```

### Data

I've already scraped FIDE tournaments and have scrapers ready for Chess Results (With over 1 Million OTB tournaments), USCF and CBX.

- Data [FIDE Tournaments JSONL](https://claude.ai/chat/4cd16316-315c-4708-8fb8-21e8032e23fe#)
- Scraper [fide_tournaments.py](https://gist.github.com/emerson-proenca/2376242967e3ad59ed9696c23a792830)

### Implementation Notes

As ornicar mentioned in this PR #18868:

> ...That's a one-time thing and doesn't need to be in lila...

The scraper is provided for reference, initial data population, and it's somewhat slow due to being sequential, I can make it async if needed. The actual API implementation would be part of the Lichess backend, or not decline if you want to.

That's about it, thank you for your time!
