# Chess Tournaments Database Archive

Chess tournament data with 387995 FIDE tournaments.

**This project is discontinued**

The data was collected by using web scraping from https://ratings.fide.com/rated_tournaments.phtml website. After [feedback](https://github.com/lichess-org/lila/issues/18989) from lichess, I've decided to discontinue at least temporary this project. The existing data is provided as-is for research, analytics, personal projects or whatever.

## Download

```bash
git clone https://github.com/emerson-proenca/OTB
cd otb
pip install -r requirements.txt
```

**Schema:**

```SQL
CREATE TABLE [tournaments] (
   [fide_id] INTEGER PRIMARY KEY,
   [name] TEXT,
   [city] TEXT,
   [s] TEXT,
   [start] TEXT,
   [country] TEXT,
   [rcvd] TEXT,
   [period] TEXT
);
```

## License

- [LICENSE MIT](https://github.com/emerson-proenca/OTB/blob/main/LICENSE) - You can use the code here for any purpose. 
- Data was collected from https://ratings.fide.com/rated_tournaments.phtml

## Contact

For questions about this archive, open an issue on GitHub.

---

I haven't abandoned this project, but I just think there's no one (outside of me) who is interested in using scraped data. Even tho FIDE doesn't doesn't have a Terms of Service and robots.txt

I have more scrapers and way more data (1.3 Million Chess Results tournaments), but I didn't show them here, because I might get isolated from the chess comunity by doing something "shady". If some people want it, I'll continue, until then it'll stay here.

If you are the owner of the data, contact me and I'll remove it.
