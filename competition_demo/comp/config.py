"""
Competition constants. This file is PUBLIC - contestants get an identical copy,
so local and organiser runs use the same scoring rules.
"""

# ---------------------------------------------------------------- market shape
N_INSTRUMENTS = 50
N_SECTORS = 6
SECTOR_NAMES = ["ENERGY", "FINL", "TECH", "HEALTH", "INDUS", "CONSUM"]

# ------------------------------------------------------------------- calendar
N_SAMPLE_DAYS = 750      # given to contestants in prices.csv
N_VALID_DAYS = 150       # hidden validation history preceding the final futures
N_PRIVATE_DAYS = 250     # hidden; the Monte Carlo futures
N_PATHS = 200            # simulated futures used for the final ranking

# ----------------------------------------------------------------- portfolio
# All positions are expressed in DOLLARS. Positive = long, negative = short.
GROSS_LIMIT = 1_000_000.0    # sum |position_i|  must be <= this
NET_LIMIT = 100_000.0        # |sum position_i|  must be <= this
CONCENTRATION_LIMIT = 100_000.0   # |position_i| must be <= this (10% of gross)

# --------------------------------------------------------------------- costs
COMMISSION_BPS = 3.0         # charged on |traded dollars| each day

# -------------------------------------------------------------------- timing
WARMUP_DAYS = 60             # strategy is not called before this index
MAX_SECONDS_PER_BACKTEST = 120.0

# -------------------------------------------------------------------- scoring
TRADING_DAYS_PER_YEAR = 252
DRAWDOWN_CAP = 0.15          # maxDD of 15% of GROSS_LIMIT zeroes the score
SCORE_PERCENTILE = 25        # final rank = this percentile across the paths
MAX_CATASTROPHIC_FRACTION = 0.05  # at most 5% of paths may reach DRAWDOWN_CAP
SHARPE_DAILY_VOL_FLOOR = 1.0  # $1/day floor: constant losses never score as flat

# Minimum capital deployment. Sharpe is scale free, so without this a team
# could trade $50k of the $1M budget, take almost no risk, and score the same
# as a team running the full book. You are given a risk budget; you are
# expected to use it. Below this, your score is prorated by how much of it you
# actually deployed.
MIN_AVG_GROSS = 0.40 * GROSS_LIMIT
