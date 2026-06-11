"""
Golden evaluation dataset for QuantSentinel.

Contains 20 academically grounded quantitative trading hypotheses used to
evaluate the Critic agent's research memos. The last 5 entries (Volatility
Regime category) serve as the held-out eval set for the nightly DSPy
prompt optimisation loop.
"""

HYPOTHESES = [
    # ----- MOMENTUM / TREND FOLLOWING -----
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a long-only monthly-rebalanced strategy on SPY that holds SPY when the trailing 12-month total return is strictly positive and is in cash (0% return) otherwise achieves a higher Sharpe ratio and a smaller maximum drawdown than buy-and-hold SPY.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.70,
     "notes": "Moskowitz, Ooi & Pedersen (2012, JFE) document robust 12-month time-series momentum; Hurst, Ooi & Pedersen (2017, JPM) extend back to 1880. Out-of-sample 2010-2024 the rule sidesteps the 2020 and most of the 2022 drawdown, raising Sharpe and lowering max drawdown."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a daily strategy that holds SPY when SPY's close is above its 200-day simple moving average and rotates to cash otherwise produces a Sharpe ratio at least 0.10 higher and a maximum drawdown materially smaller than buy-and-hold SPY.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.70,
     "notes": "Faber (2007 J. Wealth Mgmt; updated 2013) and Siegel (Stocks for the Long Run) document risk-adjusted improvement from SMA timing. The 2013 update confirmed performance held up out-of-sample; rule exits SPY in early 2020 and most of 2022."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a monthly-rebalanced cross-sectional momentum strategy on the universe {SPY, QQQ, IWM, DIA, GLD, TLT, XLF, XLE} that goes long the top-2 and short the bottom-2 by trailing 6-month total return generates statistically significant positive average monthly returns.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Asness, Moskowitz & Pedersen (2013, J. Finance) find momentum everywhere; Tse (2015, J. Financial Markets) finds it weak/insignificant in country/sector ETFs post-2009. 2022 was a major drawdown for cross-asset momentum; result is regime-dependent."},
    # ----- MEAN REVERSION -----
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a long-only daily strategy that buys SPY at the close when RSI(2) closes below 10 and exits at the close when RSI(2) closes above 70 (max 5-day holding) achieves a positive average return per trade with t-stat > 2 and hit rate above 60%.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.70,
     "notes": "Jegadeesh (1990, J. Finance) and Lehmann (1990, QJE) document short-term reversal; Da, Liu & Schaumburg (2014, Mgmt. Sci.) confirm it is significant through 2009. Index-level oversold bounces are reliable, particularly in higher-vol regimes."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a long-only strategy on SPY that buys when close < 20-day SMA - 2*sigma_20 and sells when close > 20-day SMA generates a higher CAGR than buy-and-hold SPY.",
     "expected_verdict": "reject", "min_acceptable_score": 0.70,
     "notes": "Multiple parameter-grid backtests (Bollinger 2012; recent SPY 1993-2018 studies) find no (window, sigma) combination beats buy-and-hold CAGR on US equity indices because SPY's strong upward drift dominates the in-and-out timing edge."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the first-order autocorrelation of weekly log-returns of SPY is statistically significantly negative.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Lo & MacKinlay (1988, RFS) document negative autocorrelation in weekly returns for stocks and small-cap indices but the effect is much weaker for large-cap value-weighted indices. Nagel (2012, RFS) shows short-term reversal compensation has been arbitraged away outside vol-spike regimes."},
    # ----- SEASONALITY / CALENDAR -----
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the average January return of IWM is statistically significantly higher than the average January return of SPY (one-tailed test on 15 Januaries).",
     "expected_verdict": "reject", "min_acceptable_score": 0.75,
     "notes": "Rozeff & Kinney (1976, JFE) and Banz (1981) documented small-cap January effect; Haug & Hirschey (2006, FAJ) found persistence to 2000s; Gu (2003) shows clear post-1988 decline. 2010-2024 has multiple negative IWM Januaries (2014, 2016, 2022, 2024); IWM-vs-SPY gap statistically insignificant."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the mean daily return of SPY in the 4-day turn-of-month window (last trading day plus first 3 trading days of next month) is statistically significantly higher than the mean daily return on all other days.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Lakonishok & Smidt (1988, RFS); McConnell & Xu (2008, FAJ). Recent QuantSeeker / Etula et al. (2020) work shows the classical 4-day TOM has weakened in the last decade for US equity ETFs while a broader [-1,+5] or [-1,+7] window remains marginally significant. Window-sensitive."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the average monthly return of SPY in November-April is statistically significantly higher than in May-October (Halloween effect).",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.65,
     "notes": "Bouman & Jacobsen (2002, AER); Zhang & Jacobsen (2021, JIMF) confirm out-of-sample in 65 markets with 5-8 pp gap. Direction holds in US 2010-2024 though magnitude attenuated by strong summer 2020/2024."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the average Monday close-to-close return of SPY is statistically significantly negative (one-tailed test).",
     "expected_verdict": "reject", "min_acceptable_score": 0.75,
     "notes": "French (1980, JFE) original. Schwert (2003) and Steeley (2001) document the day-of-week effect faded post-1990 and disappeared in US large-cap indices after 2000; CXO Advisory replication on SPY 1993-2017 confirms no stable Monday underperformance."},
    # ----- FOMC / MACRO -----
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the cumulative SPY return on the trading day before scheduled FOMC announcement days is statistically significantly higher than the unconditional daily mean return of SPY.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Lucca & Moench (2015, J. Finance) document strong drift through 2011; Kurov, Wolfe & Gilbert (2021, FRL) find the drift 'essentially disappeared after 2015' except on press-conference meetings. Pooled result is borderline."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the average close-to-close return of SPY on the 8 scheduled FOMC announcement days each year is statistically significantly higher than its average return on non-announcement days.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.65,
     "notes": "Savor & Wilson (2013, JFQA) document ~11 bp/day premium on FOMC, CPI, employment days. FOMC-day premium remains positive in 2010-2024 despite attenuation post-2015 (Kurov et al. 2021)."},
    # ----- FACTOR / ANOMALIES -----
    {"hypothesis": "From 2010-01-01 to 2024-12-31, IWM (Russell 2000) delivers a higher annualized total return (CAGR) than SPY (S&P 500), consistent with the small-cap premium.",
     "expected_verdict": "reject", "min_acceptable_score": 0.80,
     "notes": "Banz (1981, JFE); Fama & French (1993, JFE). Alquist, Israel & Moskowitz (2018, 'Fact, Fiction, and the Size Effect') show raw size premium insignificant since publication. 2010-2024: SPY ~13.5% vs IWM ~9.5% annualized."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, AAPL, MSFT, and AMZN each exhibit a statistically significant positive 60-day cumulative abnormal return (vs SPY) following quarterly earnings announcements where the announcement-day return exceeds +2%.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Bernard & Thomas (1989 JAR; 1990 JAE) document robust PEAD ~8-9%/quarter on SUE-sorted portfolios. Chordia, Subrahmanyam & Tong (2014, JAE) and Milian (2015) find PEAD has weakened sharply in liquid mega-caps where decimalization, ETF flows and HFT have eroded the drift."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, a monthly-rebalanced strategy that allocates 100% to whichever of {SPY, TLT, GLD} has the highest trailing 12-month total return achieves a higher Sharpe ratio than buy-and-hold SPY.",
     "expected_verdict": "inconclusive", "min_acceptable_score": 0.65,
     "notes": "Antonacci (2014) Dual Momentum; Faber (2013) GTAA. Sensitive to 2022 simultaneous SPY/TLT crash. Average Sharpe similar to or slightly below SPY buy-and-hold over 2010-2024 because SPY trended strongly."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, an equal-weighted portfolio of {AAPL, MSFT} (lower realized volatility, large-cap quality) achieves a higher Sharpe ratio than IWM (high-vol small caps), consistent with the low-volatility/quality anomaly.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.70,
     "notes": "Ang, Hodrick, Xing & Zhang (2006, J. Finance); Frazzini & Pedersen (2014, JFE) BAB. AAPL/MSFT in 2010-2024 had lower realized vol than IWM and dramatically higher returns, generalizing low-vol intuition. Caveat: also reflects MAG-7 secular trend."},
    # ----- VOLATILITY REGIME (items 16-20 = held-out eval set for nightly optimizer) -----
    {"hypothesis": "From 2010-02-01 to 2024-12-31, a long buy-and-hold position in VXX (split-adjusted, including VXXB successor) achieves a negative annualized total return of at least -30% per year, driven by negative roll yield from VIX-futures contango.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.80,
     "notes": "VIX futures curve in contango ~80% of trading days. Mechanical roll cost causes structural decay (Whaley 2013, JPM; Alexander & Korovilas 2012). Original VXX lost >99% before being delisted. One of the most robust patterns in modern markets."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the first-order autocorrelation of squared daily log-returns of SPY is statistically significantly positive (Ljung-Box on squared returns rejects no-serial-correlation null at 1%), evidencing volatility clustering.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.80,
     "notes": "Engle (1982, Econometrica); Bollerslev (1986, J. Econometrics); Cont (2001, Quant. Finance). Volatility clustering is a universal stylized fact; persistence parameter typically alpha+beta ~0.95-0.98 in GARCH(1,1) on SPY."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the Pearson correlation between daily log-returns of SPY and daily changes in ^VIX is statistically significantly negative and below -0.50.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.80,
     "notes": "Black (1976) leverage effect; Bouchaud, Matacz & Potters (2001). Empirical SPY/VIX daily-change correlation reliably -0.70 to -0.85 every year of 2010-2024 due to leverage, volatility-feedback, and the mechanical link via SPX option premia."},
    {"hypothesis": "From 2010-01-01 to 2024-12-31, the average 20-trading-day forward return of SPY conditional on ^VIX closing above 30 is statistically significantly higher than the unconditional 20-day forward return of SPY.",
     "expected_verdict": "cannot_reject", "min_acceptable_score": 0.65,
     "notes": "Whaley (2009 JPM) frames VIX as mean-reverting fear index; Nagel (2012 RFS) shows short-term reversal returns are predictable by VIX (compensation for liquidity provision when intermediaries are constrained). High-VIX events 2011/2015/2018/2020/2022 followed on average by positive 20-day SPY returns, but small N makes inference noisy."},
]

# Alias used by nightly_optimizer.py and suggestion_engine.py
GOLDEN_DATASET = HYPOTHESES

# Training set: first 15 hypotheses (used by DSPy BootstrapFewShot)
GOLDEN_TRAIN = HYPOTHESES[:15]

# Held-out eval set: last 5 (Volatility Regime — never seen during optimisation)
GOLDEN_HELDOUT = HYPOTHESES[15:]
