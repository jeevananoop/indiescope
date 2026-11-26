# IndieScope: Project Framing

## User story
As an independent game developer, I want to enter my budget, the selling price of my game and its tags, so that I can find out whether my game is likely to earn enough to cover my budget.

## Acceptance criterion
If I enter the tags Indie and Roguelike, a price of $15 and a budget of $50,000, then the tool displays:
- an estimated revenue range (for example, $20,000 to $150,000, illustrative figures);
- the probability of covering my budget;
- a verdict: GO, RISKY or NO-GO.

## Running example
A 2-person studio with a **$60,000 budget** hesitates between two concepts sold at **$15**:
- **A**: a roguelike (tags Indie + Roguelike);
- **B**: a cozy game (tags Indie + Cozy).

Result (`notebooks/05_simulator.ipynb`): both are **RISKY**. The cozy game has better odds (40 % vs 32 % of comparable games covered $60,000) and stays RISKY in all 3 scenarios, while the roguelike drops to NO-GO in the low scenario. Recommended price: $15-20 for the cozy game, $20-30 for the roguelike.

## Core features (what happens if it is missing)
| Feature | If it were missing |
|---|---|
| Load and clean `games.csv` | The tool has no data to analyse, so it cannot compute or compare anything. |
| Compute net revenue | The tool cannot tell how much comparable games earned, so it cannot compare that with the developer's budget. |
| Find comparable games | The answer would not depend on the developer's type of game, so it would not be useful. |
| Compute the probability of covering the budget | The tool cannot say whether the game is likely to be profitable. |

## Should-have feature (useful, but not core)
- GO / RISKY / NO-GO verdict: the probability already answers the user story; the verdict only makes it easier to read.

## Data contract (`data/games_clean.csv`)
Produced by `clean_games()` in `src/cleaning.py`. One row per paid, tagged game released on Steam between 2015 and 6 months before the data snapshot (March 2026).

| Column | Type | Meaning | Source column |
|---|---|---|---|
| `app_id` | int | Unique Steam identifier | AppID |
| `name` | str | Game name | Name |
| `release_date` | date | Release date | Release date (`"Aug 1, 2023"`) |
| `release_year` | int | Release year (2015 or later) | derived from Release date |
| `price` | float | Full price in USD, always > 0 | Price |
| `positive` | int | Number of positive reviews | Positive |
| `negative` | int | Number of negative reviews | Negative |
| `owners_min` | int | Lower bound of SteamSpy owners | Estimated owners (`"20000 - 50000"`) |
| `owners_max` | int | Upper bound of SteamSpy owners | Estimated owners |
| `tags` | str | User tags, separated by a single comma, no spaces around | Tags |

**Data quality trap 1**: the raw header has 39 names, but each row has 40 values (`DiscountDLC count` should be `Discount` and `DLC count`). `load_games()` fixes this by passing the 40 correct names to `pd.read_csv`.

**Data quality trap 2**: `Price` is the price on the day of collection, discount included (41 % of paid games were on sale; Hollow Knight shows $7.49 at -50 %). `clean_games()` restores the full price: `price / (1 - discount / 100)`.

## Hypotheses
| Hypothesis | Value | Source / justification |
|---|---|---|
| Sales per review (Boxleiter method) | 20 / 40 / 60 (low / mid / high) | Industry rule of thumb, validated in `notebooks/03_estimation.ipynb` (see below) |
| Steam commission | 30 % | Steam standard revenue share (below $10M of revenue) |
| Refunds | 10 % of sales | Order of magnitude; Steam refunds games played < 2 h within 14 days |
| Average price paid | 75 % of full price | Many copies are sold during Steam sales |
| Comparable games | Games that share all the selected tags | Tags are the only genre information in the dataset |
| Start year | 2015 | Before that, Steam was curated and released < 2,500 games/year |
| Minimum age of a game | 6 months | Reviews take time to come in |

### Validation of the multiplier and decision
- **SteamSpy**: on the 18,950 games with at least 20,000 owners, `sales_mid` falls inside the SteamSpy owners range for 14 % of games, below it for 83 %, above it for 3 %. The median owners/review ratio is 245, but it is biased by small games (cheap games get bundled and given away). For games with 1,000-10,000 reviews the ratio is 72, and 48 above 10,000 reviews. Since owners ≥ sales, 40-60 sales per review remains plausible.
- **Known games** (official figures vs our Steam-only estimate):

| Game | Official sales | Source | Our low / mid estimate | Gap (mid) |
|---|---|---|---|---|
| Valheim | 10 M (April 2022, PC) | [PC Gamer](https://www.pcgamer.com/valheim-has-sold-over-10-million-copies) | 10.0 M / 20.0 M | +100 % |
| Balatro | 5 M (Jan 2025, all platforms) | [Gematsu](https://www.gematsu.com/2025/01/balatro-sales-top-five-million) | 3.1 M / 6.1 M | +23 % |
| Hollow Knight | 15 M (Aug 2025, all platforms) | [AV Club](https://www.avclub.com/hollow-knight-hits-all-time-peak-player-count-sells-15-million-copies) | 8.3 M / 16.6 M | +11 % |

- **Decision**: keep 20 / 40 / 60. Our estimate is below SteamSpy for most games, i.e. prudent, which is the right direction of error for a tool that advises spending a budget. For big hits, the low scenario is the most accurate.

## Known limitations
- The tool sees neither marketing nor game quality: two games with the same tags and price can earn very different amounts.
- Free-to-play games are excluded: their revenue comes from in-game purchases, not from the price.
- Owners are not sales: SteamSpy owners include gifted keys, bundles and free weekends.
- The reviews/sales ratio varies by genre and by game size (very popular games get more reviews per buyer).
- Survivorship bias: games removed from Steam are not in the dataset, so failures are under-represented and the probabilities are slightly optimistic.
- The dataset is a snapshot (March 2026): reviews keep coming in after that date.
