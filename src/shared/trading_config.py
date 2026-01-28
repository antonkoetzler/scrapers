"""
Centralized trading configuration for stocks and crypto scrapers.

This file defines the stocks and cryptocurrencies that should be scraped.
Assets are organized by priority and category.
"""

# Primary stocks (major indices - S&P 500, NASDAQ, Dow components)
PRIMARY_STOCKS = {
    # Technology
    'AAPL': {
        'alpha_vantage': 'AAPL',
        'yfinance': 'AAPL',
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'exchange': 'NASDAQ'
    },
    'MSFT': {
        'alpha_vantage': 'MSFT',
        'yfinance': 'MSFT',
        'sector': 'Technology',
        'industry': 'Software',
        'exchange': 'NASDAQ'
    },
    'GOOGL': {
        'alpha_vantage': 'GOOGL',
        'yfinance': 'GOOGL',
        'sector': 'Technology',
        'industry': 'Internet Content & Information',
        'exchange': 'NASDAQ'
    },
    'AMZN': {
        'alpha_vantage': 'AMZN',
        'yfinance': 'AMZN',
        'sector': 'Consumer Cyclical',
        'industry': 'E-commerce',
        'exchange': 'NASDAQ'
    },
    'NVDA': {
        'alpha_vantage': 'NVDA',
        'yfinance': 'NVDA',
        'sector': 'Technology',
        'industry': 'Semiconductors',
        'exchange': 'NASDAQ'
    },
    'META': {
        'alpha_vantage': 'META',
        'yfinance': 'META',
        'sector': 'Technology',
        'industry': 'Social Media',
        'exchange': 'NASDAQ'
    },
    'TSLA': {
        'alpha_vantage': 'TSLA',
        'yfinance': 'TSLA',
        'sector': 'Consumer Cyclical',
        'industry': 'Auto Manufacturers',
        'exchange': 'NASDAQ'
    },
    'NFLX': {
        'alpha_vantage': 'NFLX',
        'yfinance': 'NFLX',
        'sector': 'Communication Services',
        'industry': 'Entertainment',
        'exchange': 'NASDAQ'
    },
    'AMD': {
        'alpha_vantage': 'AMD',
        'yfinance': 'AMD',
        'sector': 'Technology',
        'industry': 'Semiconductors',
        'exchange': 'NASDAQ'
    },
    'INTC': {
        'alpha_vantage': 'INTC',
        'yfinance': 'INTC',
        'sector': 'Technology',
        'industry': 'Semiconductors',
        'exchange': 'NASDAQ'
    },
    'CRM': {
        'alpha_vantage': 'CRM',
        'yfinance': 'CRM',
        'sector': 'Technology',
        'industry': 'Software',
        'exchange': 'NYSE'
    },
    'ORCL': {
        'alpha_vantage': 'ORCL',
        'yfinance': 'ORCL',
        'sector': 'Technology',
        'industry': 'Software',
        'exchange': 'NYSE'
    },
    'ADBE': {
        'alpha_vantage': 'ADBE',
        'yfinance': 'ADBE',
        'sector': 'Technology',
        'industry': 'Software',
        'exchange': 'NASDAQ'
    },
    'CSCO': {
        'alpha_vantage': 'CSCO',
        'yfinance': 'CSCO',
        'sector': 'Technology',
        'industry': 'Communication Equipment',
        'exchange': 'NASDAQ'
    },
    
    # Finance
    'JPM': {
        'alpha_vantage': 'JPM',
        'yfinance': 'JPM',
        'sector': 'Financial Services',
        'industry': 'Banks',
        'exchange': 'NYSE'
    },
    'BAC': {
        'alpha_vantage': 'BAC',
        'yfinance': 'BAC',
        'sector': 'Financial Services',
        'industry': 'Banks',
        'exchange': 'NYSE'
    },
    'WFC': {
        'alpha_vantage': 'WFC',
        'yfinance': 'WFC',
        'sector': 'Financial Services',
        'industry': 'Banks',
        'exchange': 'NYSE'
    },
    'GS': {
        'alpha_vantage': 'GS',
        'yfinance': 'GS',
        'sector': 'Financial Services',
        'industry': 'Capital Markets',
        'exchange': 'NYSE'
    },
    'MS': {
        'alpha_vantage': 'MS',
        'yfinance': 'MS',
        'sector': 'Financial Services',
        'industry': 'Capital Markets',
        'exchange': 'NYSE'
    },
    'V': {
        'alpha_vantage': 'V',
        'yfinance': 'V',
        'sector': 'Financial Services',
        'industry': 'Credit Services',
        'exchange': 'NYSE'
    },
    'MA': {
        'alpha_vantage': 'MA',
        'yfinance': 'MA',
        'sector': 'Financial Services',
        'industry': 'Credit Services',
        'exchange': 'NYSE'
    },
    
    # Healthcare
    'JNJ': {
        'alpha_vantage': 'JNJ',
        'yfinance': 'JNJ',
        'sector': 'Healthcare',
        'industry': 'Drug Manufacturers',
        'exchange': 'NYSE'
    },
    'UNH': {
        'alpha_vantage': 'UNH',
        'yfinance': 'UNH',
        'sector': 'Healthcare',
        'industry': 'Healthcare Plans',
        'exchange': 'NYSE'
    },
    'PFE': {
        'alpha_vantage': 'PFE',
        'yfinance': 'PFE',
        'sector': 'Healthcare',
        'industry': 'Drug Manufacturers',
        'exchange': 'NYSE'
    },
    'ABBV': {
        'alpha_vantage': 'ABBV',
        'yfinance': 'ABBV',
        'sector': 'Healthcare',
        'industry': 'Drug Manufacturers',
        'exchange': 'NYSE'
    },
    'TMO': {
        'alpha_vantage': 'TMO',
        'yfinance': 'TMO',
        'sector': 'Healthcare',
        'industry': 'Diagnostics & Research',
        'exchange': 'NYSE'
    },
    
    # Consumer
    'WMT': {
        'alpha_vantage': 'WMT',
        'yfinance': 'WMT',
        'sector': 'Consumer Defensive',
        'industry': 'Discount Stores',
        'exchange': 'NYSE'
    },
    'HD': {
        'alpha_vantage': 'HD',
        'yfinance': 'HD',
        'sector': 'Consumer Cyclical',
        'industry': 'Home Improvement Retail',
        'exchange': 'NYSE'
    },
    'PG': {
        'alpha_vantage': 'PG',
        'yfinance': 'PG',
        'sector': 'Consumer Defensive',
        'industry': 'Household & Personal Products',
        'exchange': 'NYSE'
    },
    'KO': {
        'alpha_vantage': 'KO',
        'yfinance': 'KO',
        'sector': 'Consumer Defensive',
        'industry': 'Beverages',
        'exchange': 'NYSE'
    },
    'PEP': {
        'alpha_vantage': 'PEP',
        'yfinance': 'PEP',
        'sector': 'Consumer Defensive',
        'industry': 'Beverages',
        'exchange': 'NASDAQ'
    },
    'MCD': {
        'alpha_vantage': 'MCD',
        'yfinance': 'MCD',
        'sector': 'Consumer Cyclical',
        'industry': 'Restaurants',
        'exchange': 'NYSE'
    },
    'NKE': {
        'alpha_vantage': 'NKE',
        'yfinance': 'NKE',
        'sector': 'Consumer Cyclical',
        'industry': 'Footwear & Accessories',
        'exchange': 'NYSE'
    },
    
    # Energy
    'XOM': {
        'alpha_vantage': 'XOM',
        'yfinance': 'XOM',
        'sector': 'Energy',
        'industry': 'Oil & Gas',
        'exchange': 'NYSE'
    },
    'CVX': {
        'alpha_vantage': 'CVX',
        'yfinance': 'CVX',
        'sector': 'Energy',
        'industry': 'Oil & Gas',
        'exchange': 'NYSE'
    },
    
    # Industrial
    'BA': {
        'alpha_vantage': 'BA',
        'yfinance': 'BA',
        'sector': 'Industrials',
        'industry': 'Aerospace & Defense',
        'exchange': 'NYSE'
    },
    'CAT': {
        'alpha_vantage': 'CAT',
        'yfinance': 'CAT',
        'sector': 'Industrials',
        'industry': 'Farm & Heavy Construction Machinery',
        'exchange': 'NYSE'
    },
    'GE': {
        'alpha_vantage': 'GE',
        'yfinance': 'GE',
        'sector': 'Industrials',
        'industry': 'Specialty Industrial Machinery',
        'exchange': 'NYSE'
    },
    
    # Communication
    'DIS': {
        'alpha_vantage': 'DIS',
        'yfinance': 'DIS',
        'sector': 'Communication Services',
        'industry': 'Entertainment',
        'exchange': 'NYSE'
    },
    'CMCSA': {
        'alpha_vantage': 'CMCSA',
        'yfinance': 'CMCSA',
        'sector': 'Communication Services',
        'industry': 'Telecom Services',
        'exchange': 'NASDAQ'
    },
    'T': {
        'alpha_vantage': 'T',
        'yfinance': 'T',
        'sector': 'Communication Services',
        'industry': 'Telecom Services',
        'exchange': 'NYSE'
    },
    'VZ': {
        'alpha_vantage': 'VZ',
        'yfinance': 'VZ',
        'sector': 'Communication Services',
        'industry': 'Telecom Services',
        'exchange': 'NYSE'
    },
}

# Secondary stocks (mid-cap and additional major stocks)
SECONDARY_STOCKS = {
    # Technology
    'SNOW': {'alpha_vantage': 'SNOW', 'yfinance': 'SNOW', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'ZM': {'alpha_vantage': 'ZM', 'yfinance': 'ZM', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NASDAQ'},
    'DOCN': {'alpha_vantage': 'DOCN', 'yfinance': 'DOCN', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'NET': {'alpha_vantage': 'NET', 'yfinance': 'NET', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'SQ': {'alpha_vantage': 'SQ', 'yfinance': 'SQ', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'PYPL': {'alpha_vantage': 'PYPL', 'yfinance': 'PYPL', 'sector': 'Technology', 'industry': 'Credit Services', 'exchange': 'NASDAQ'},
    'SHOP': {'alpha_vantage': 'SHOP', 'yfinance': 'SHOP', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'UBER': {'alpha_vantage': 'UBER', 'yfinance': 'UBER', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'LYFT': {'alpha_vantage': 'LYFT', 'yfinance': 'LYFT', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NASDAQ'},
    'RBLX': {'alpha_vantage': 'RBLX', 'yfinance': 'RBLX', 'sector': 'Technology', 'industry': 'Electronic Gaming & Multimedia', 'exchange': 'NYSE'},
    'SPOT': {'alpha_vantage': 'SPOT', 'yfinance': 'SPOT', 'sector': 'Communication Services', 'industry': 'Entertainment', 'exchange': 'NYSE'},
    
    # Finance
    'C': {'alpha_vantage': 'C', 'yfinance': 'C', 'sector': 'Financial Services', 'industry': 'Banks', 'exchange': 'NYSE'},
    'AXP': {'alpha_vantage': 'AXP', 'yfinance': 'AXP', 'sector': 'Financial Services', 'industry': 'Credit Services', 'exchange': 'NYSE'},
    'BLK': {'alpha_vantage': 'BLK', 'yfinance': 'BLK', 'sector': 'Financial Services', 'industry': 'Asset Management', 'exchange': 'NYSE'},
    
    # Healthcare
    'LLY': {'alpha_vantage': 'LLY', 'yfinance': 'LLY', 'sector': 'Healthcare', 'industry': 'Drug Manufacturers', 'exchange': 'NYSE'},
    'MRK': {'alpha_vantage': 'MRK', 'yfinance': 'MRK', 'sector': 'Healthcare', 'industry': 'Drug Manufacturers', 'exchange': 'NYSE'},
    'BMY': {'alpha_vantage': 'BMY', 'yfinance': 'BMY', 'sector': 'Healthcare', 'industry': 'Drug Manufacturers', 'exchange': 'NYSE'},
    'GILD': {'alpha_vantage': 'GILD', 'yfinance': 'GILD', 'sector': 'Healthcare', 'industry': 'Biotechnology', 'exchange': 'NASDAQ'},
    'AMGN': {'alpha_vantage': 'AMGN', 'yfinance': 'AMGN', 'sector': 'Healthcare', 'industry': 'Biotechnology', 'exchange': 'NASDAQ'},
    'BIIB': {'alpha_vantage': 'BIIB', 'yfinance': 'BIIB', 'sector': 'Healthcare', 'industry': 'Biotechnology', 'exchange': 'NASDAQ'},
    
    # Consumer
    'SBUX': {'alpha_vantage': 'SBUX', 'yfinance': 'SBUX', 'sector': 'Consumer Cyclical', 'industry': 'Restaurants', 'exchange': 'NASDAQ'},
    'TGT': {'alpha_vantage': 'TGT', 'yfinance': 'TGT', 'sector': 'Consumer Cyclical', 'industry': 'Department Stores', 'exchange': 'NYSE'},
    'LOW': {'alpha_vantage': 'LOW', 'yfinance': 'LOW', 'sector': 'Consumer Cyclical', 'industry': 'Home Improvement Retail', 'exchange': 'NYSE'},
    'COST': {'alpha_vantage': 'COST', 'yfinance': 'COST', 'sector': 'Consumer Defensive', 'industry': 'Discount Stores', 'exchange': 'NASDAQ'},
    
    # Energy
    'SLB': {'alpha_vantage': 'SLB', 'yfinance': 'SLB', 'sector': 'Energy', 'industry': 'Oil & Gas Equipment & Services', 'exchange': 'NYSE'},
    'COP': {'alpha_vantage': 'COP', 'yfinance': 'COP', 'sector': 'Energy', 'industry': 'Oil & Gas', 'exchange': 'NYSE'},
    
    # Industrial
    'HON': {'alpha_vantage': 'HON', 'yfinance': 'HON', 'sector': 'Industrials', 'industry': 'Specialty Industrial Machinery', 'exchange': 'NASDAQ'},
    'RTX': {'alpha_vantage': 'RTX', 'yfinance': 'RTX', 'sector': 'Industrials', 'industry': 'Aerospace & Defense', 'exchange': 'NYSE'},
    'LMT': {'alpha_vantage': 'LMT', 'yfinance': 'LMT', 'sector': 'Industrials', 'industry': 'Aerospace & Defense', 'exchange': 'NYSE'},
    'NOC': {'alpha_vantage': 'NOC', 'yfinance': 'NOC', 'sector': 'Industrials', 'industry': 'Aerospace & Defense', 'exchange': 'NYSE'},
    
    # Materials
    'LIN': {'alpha_vantage': 'LIN', 'yfinance': 'LIN', 'sector': 'Basic Materials', 'industry': 'Specialty Chemicals', 'exchange': 'NYSE'},
    'APD': {'alpha_vantage': 'APD', 'yfinance': 'APD', 'sector': 'Basic Materials', 'industry': 'Specialty Chemicals', 'exchange': 'NYSE'},
    
    # Utilities
    'NEE': {'alpha_vantage': 'NEE', 'yfinance': 'NEE', 'sector': 'Utilities', 'industry': 'Utilities—Renewable', 'exchange': 'NYSE'},
    'DUK': {'alpha_vantage': 'DUK', 'yfinance': 'DUK', 'sector': 'Utilities', 'industry': 'Utilities—Regulated Electric', 'exchange': 'NYSE'},
}

# Regional stocks (international markets)
REGIONAL_STOCKS = {
    # European
    'ASML': {'alpha_vantage': 'ASML', 'yfinance': 'ASML', 'sector': 'Technology', 'industry': 'Semiconductors', 'exchange': 'NASDAQ'},
    'SAP': {'alpha_vantage': 'SAP', 'yfinance': 'SAP', 'sector': 'Technology', 'industry': 'Software', 'exchange': 'NYSE'},
    'NVO': {'alpha_vantage': 'NVO', 'yfinance': 'NVO', 'sector': 'Healthcare', 'industry': 'Biotechnology', 'exchange': 'NYSE'},
    
    # Asian
    'TSM': {'alpha_vantage': 'TSM', 'yfinance': 'TSM', 'sector': 'Technology', 'industry': 'Semiconductors', 'exchange': 'NYSE'},
    'BABA': {'alpha_vantage': 'BABA', 'yfinance': 'BABA', 'sector': 'Consumer Cyclical', 'industry': 'E-commerce', 'exchange': 'NYSE'},
    'JD': {'alpha_vantage': 'JD', 'yfinance': 'JD', 'sector': 'Consumer Cyclical', 'industry': 'E-commerce', 'exchange': 'NASDAQ'},
    'PDD': {'alpha_vantage': 'PDD', 'yfinance': 'PDD', 'sector': 'Consumer Cyclical', 'industry': 'E-commerce', 'exchange': 'NASDAQ'},
}

# Combine all stocks
ALL_STOCKS = {**PRIMARY_STOCKS, **SECONDARY_STOCKS, **REGIONAL_STOCKS}

# Primary crypto (major cryptocurrencies)
PRIMARY_CRYPTO = {
    'BTC': {
        'coingecko_id': 'bitcoin',
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'category': 'Layer 1'
    },
    'ETH': {
        'coingecko_id': 'ethereum',
        'symbol': 'ETH',
        'name': 'Ethereum',
        'category': 'Layer 1'
    },
    'BNB': {
        'coingecko_id': 'binancecoin',
        'symbol': 'BNB',
        'name': 'BNB',
        'category': 'Exchange Token'
    },
    'SOL': {
        'coingecko_id': 'solana',
        'symbol': 'SOL',
        'name': 'Solana',
        'category': 'Layer 1'
    },
    'XRP': {
        'coingecko_id': 'ripple',
        'symbol': 'XRP',
        'name': 'XRP',
        'category': 'Payment'
    },
    'ADA': {
        'coingecko_id': 'cardano',
        'symbol': 'ADA',
        'name': 'Cardano',
        'category': 'Layer 1'
    },
    'DOGE': {
        'coingecko_id': 'dogecoin',
        'symbol': 'DOGE',
        'name': 'Dogecoin',
        'category': 'Meme'
    },
    'DOT': {
        'coingecko_id': 'polkadot',
        'symbol': 'DOT',
        'name': 'Polkadot',
        'category': 'Layer 1'
    },
    'AVAX': {
        'coingecko_id': 'avalanche-2',
        'symbol': 'AVAX',
        'name': 'Avalanche',
        'category': 'Layer 1'
    },
    'MATIC': {
        'coingecko_id': 'matic-network',
        'symbol': 'MATIC',
        'name': 'Polygon',
        'category': 'Layer 2'
    },
    'LINK': {
        'coingecko_id': 'chainlink',
        'symbol': 'LINK',
        'name': 'Chainlink',
        'category': 'Oracle'
    },
    'UNI': {
        'coingecko_id': 'uniswap',
        'symbol': 'UNI',
        'name': 'Uniswap',
        'category': 'DeFi'
    },
    'ATOM': {
        'coingecko_id': 'cosmos',
        'symbol': 'ATOM',
        'name': 'Cosmos',
        'category': 'Layer 1'
    },
    'LTC': {
        'coingecko_id': 'litecoin',
        'symbol': 'LTC',
        'name': 'Litecoin',
        'category': 'Payment'
    },
    'ETC': {
        'coingecko_id': 'ethereum-classic',
        'symbol': 'ETC',
        'name': 'Ethereum Classic',
        'category': 'Layer 1'
    },
}

# Secondary crypto (established altcoins)
SECONDARY_CRYPTO = {
    'XLM': {'coingecko_id': 'stellar', 'symbol': 'XLM', 'name': 'Stellar', 'category': 'Payment'},
    'ALGO': {'coingecko_id': 'algorand', 'symbol': 'ALGO', 'name': 'Algorand', 'category': 'Layer 1'},
    'VET': {'coingecko_id': 'vechain', 'symbol': 'VET', 'name': 'VeChain', 'category': 'Enterprise'},
    'FIL': {'coingecko_id': 'filecoin', 'symbol': 'FIL', 'name': 'Filecoin', 'category': 'Storage'},
    'TRX': {'coingecko_id': 'tron', 'symbol': 'TRX', 'name': 'TRON', 'category': 'Layer 1'},
    'NEAR': {'coingecko_id': 'near', 'symbol': 'NEAR', 'name': 'NEAR Protocol', 'category': 'Layer 1'},
    'APT': {'coingecko_id': 'aptos', 'symbol': 'APT', 'name': 'Aptos', 'category': 'Layer 1'},
    'SUI': {'coingecko_id': 'sui', 'symbol': 'SUI', 'name': 'Sui', 'category': 'Layer 1'},
    'ARB': {'coingecko_id': 'arbitrum', 'symbol': 'ARB', 'name': 'Arbitrum', 'category': 'Layer 2'},
    'OP': {'coingecko_id': 'optimism', 'symbol': 'OP', 'name': 'Optimism', 'category': 'Layer 2'},
    'AAVE': {'coingecko_id': 'aave', 'symbol': 'AAVE', 'name': 'Aave', 'category': 'DeFi'},
    'MKR': {'coingecko_id': 'maker', 'symbol': 'MKR', 'name': 'Maker', 'category': 'DeFi'},
    'COMP': {'coingecko_id': 'compound-governance-token', 'symbol': 'COMP', 'name': 'Compound', 'category': 'DeFi'},
    'SNX': {'coingecko_id': 'havven', 'symbol': 'SNX', 'name': 'Synthetix', 'category': 'DeFi'},
    'CRV': {'coingecko_id': 'curve-dao-token', 'symbol': 'CRV', 'name': 'Curve DAO', 'category': 'DeFi'},
    '1INCH': {'coingecko_id': '1inch', 'symbol': '1INCH', 'name': '1inch Network', 'category': 'DeFi'},
    'SUSHI': {'coingecko_id': 'sushi', 'symbol': 'SUSHI', 'name': 'SushiSwap', 'category': 'DeFi'},
    'YFI': {'coingecko_id': 'yearn-finance', 'symbol': 'YFI', 'name': 'yearn.finance', 'category': 'DeFi'},
    'GRT': {'coingecko_id': 'the-graph', 'symbol': 'GRT', 'name': 'The Graph', 'category': 'Indexing'},
    'RENDER': {'coingecko_id': 'render-token', 'symbol': 'RENDER', 'name': 'Render', 'category': 'Compute'},
    'INJ': {'coingecko_id': 'injective-protocol', 'symbol': 'INJ', 'name': 'Injective', 'category': 'Layer 1'},
    'TIA': {'coingecko_id': 'celestia', 'symbol': 'TIA', 'name': 'Celestia', 'category': 'Infrastructure'},
    'SEI': {'coingecko_id': 'sei-network', 'symbol': 'SEI', 'name': 'Sei', 'category': 'Layer 1'},
    'FTM': {'coingecko_id': 'fantom', 'symbol': 'FTM', 'name': 'Fantom', 'category': 'Layer 1'},
    'ICP': {'coingecko_id': 'internet-computer', 'symbol': 'ICP', 'name': 'Internet Computer', 'category': 'Layer 1'},
    'THETA': {'coingecko_id': 'theta-token', 'symbol': 'THETA', 'name': 'Theta Network', 'category': 'Media'},
    'EOS': {'coingecko_id': 'eos', 'symbol': 'EOS', 'name': 'EOS', 'category': 'Layer 1'},
    'XTZ': {'coingecko_id': 'tezos', 'symbol': 'XTZ', 'name': 'Tezos', 'category': 'Layer 1'},
    'HBAR': {'coingecko_id': 'hedera-hashgraph', 'symbol': 'HBAR', 'name': 'Hedera', 'category': 'Layer 1'},
    'QNT': {'coingecko_id': 'quant-network', 'symbol': 'QNT', 'name': 'Quant', 'category': 'Interoperability'},
    'IMX': {'coingecko_id': 'immutable-x', 'symbol': 'IMX', 'name': 'Immutable X', 'category': 'Layer 2'},
    'LRC': {'coingecko_id': 'loopring', 'symbol': 'LRC', 'name': 'Loopring', 'category': 'Layer 2'},
    'ZEC': {'coingecko_id': 'zcash', 'symbol': 'ZEC', 'name': 'Zcash', 'category': 'Privacy'},
    'DASH': {'coingecko_id': 'dash', 'symbol': 'DASH', 'name': 'Dash', 'category': 'Payment'},
    'BCH': {'coingecko_id': 'bitcoin-cash', 'symbol': 'BCH', 'name': 'Bitcoin Cash', 'category': 'Payment'},
    'XMR': {'coingecko_id': 'monero', 'symbol': 'XMR', 'name': 'Monero', 'category': 'Privacy'},
    'WAVES': {'coingecko_id': 'waves', 'symbol': 'WAVES', 'name': 'Waves', 'category': 'Layer 1'},
    'ZIL': {'coingecko_id': 'zilliqa', 'symbol': 'ZIL', 'name': 'Zilliqa', 'category': 'Layer 1'},
    'ENJ': {'coingecko_id': 'enjincoin', 'symbol': 'ENJ', 'name': 'Enjin Coin', 'category': 'Gaming'},
    'MANA': {'coingecko_id': 'decentraland', 'symbol': 'MANA', 'name': 'Decentraland', 'category': 'Metaverse'},
    'SAND': {'coingecko_id': 'the-sandbox', 'symbol': 'SAND', 'name': 'The Sandbox', 'category': 'Metaverse'},
    'AXS': {'coingecko_id': 'axie-infinity', 'symbol': 'AXS', 'name': 'Axie Infinity', 'category': 'Gaming'},
    'CHZ': {'coingecko_id': 'chiliz', 'symbol': 'CHZ', 'name': 'Chiliz', 'category': 'Sports'},
    'FLOW': {'coingecko_id': 'flow', 'symbol': 'FLOW', 'name': 'Flow', 'category': 'Layer 1'},
    'KLAY': {'coingecko_id': 'klay-token', 'symbol': 'KLAY', 'name': 'Klaytn', 'category': 'Layer 1'},
    'EGLD': {'coingecko_id': 'elrond-erd-2', 'symbol': 'EGLD', 'name': 'MultiversX', 'category': 'Layer 1'},
    'ROSE': {'coingecko_id': 'oasis-network', 'symbol': 'ROSE', 'name': 'Oasis Network', 'category': 'Layer 1'},
    'IOTA': {'coingecko_id': 'iota', 'symbol': 'IOTA', 'name': 'IOTA', 'category': 'Layer 1'},
    'HNT': {'coingecko_id': 'helium', 'symbol': 'HNT', 'name': 'Helium', 'category': 'IoT'},
    'RUNE': {'coingecko_id': 'thorchain', 'symbol': 'RUNE', 'name': 'THORChain', 'category': 'DeFi'},
    'KAVA': {'coingecko_id': 'kava', 'symbol': 'KAVA', 'name': 'Kava', 'category': 'Layer 1'},
    'OSMO': {'coingecko_id': 'osmosis', 'symbol': 'OSMO', 'name': 'Osmosis', 'category': 'DeFi'},
    'JUNO': {'coingecko_id': 'juno-network', 'symbol': 'JUNO', 'name': 'Juno Network', 'category': 'Layer 1'},
    'LUNA': {'coingecko_id': 'terra-luna', 'symbol': 'LUNA', 'name': 'Terra', 'category': 'Layer 1'},
    'USTC': {'coingecko_id': 'terrausd', 'symbol': 'USTC', 'name': 'TerraUSD Classic', 'category': 'Stablecoin'},
    'UST': {'coingecko_id': 'terrausd', 'symbol': 'UST', 'name': 'TerraUSD', 'category': 'Stablecoin'},
    'LUNC': {'coingecko_id': 'terra-luna-2', 'symbol': 'LUNC', 'name': 'Terra Classic', 'category': 'Layer 1'},
}

# Stablecoins
STABLECOINS = {
    'USDT': {'coingecko_id': 'tether', 'symbol': 'USDT', 'name': 'Tether', 'category': 'Stablecoin'},
    'USDC': {'coingecko_id': 'usd-coin', 'symbol': 'USDC', 'name': 'USD Coin', 'category': 'Stablecoin'},
    'DAI': {'coingecko_id': 'dai', 'symbol': 'DAI', 'name': 'Dai', 'category': 'Stablecoin'},
    'BUSD': {'coingecko_id': 'binance-usd', 'symbol': 'BUSD', 'name': 'Binance USD', 'category': 'Stablecoin'},
    'TUSD': {'coingecko_id': 'true-usd', 'symbol': 'TUSD', 'name': 'TrueUSD', 'category': 'Stablecoin'},
    'USDP': {'coingecko_id': 'paxos-standard', 'symbol': 'USDP', 'name': 'Pax Dollar', 'category': 'Stablecoin'},
    'FRAX': {'coingecko_id': 'frax', 'symbol': 'FRAX', 'name': 'Frax', 'category': 'Stablecoin'},
    'LUSD': {'coingecko_id': 'liquity-usd', 'symbol': 'LUSD', 'name': 'Liquity USD', 'category': 'Stablecoin'},
}

# Combine all crypto
ALL_CRYPTO = {**PRIMARY_CRYPTO, **SECONDARY_CRYPTO, **STABLECOINS}

# Helper functions
def get_all_stocks() -> dict:
    """Get all stock configurations."""
    return ALL_STOCKS

def get_primary_stocks() -> dict:
    """Get primary stock configurations."""
    return PRIMARY_STOCKS

def get_secondary_stocks() -> dict:
    """Get secondary stock configurations."""
    return SECONDARY_STOCKS

def get_regional_stocks() -> dict:
    """Get regional stock configurations."""
    return REGIONAL_STOCKS

def get_all_crypto() -> dict:
    """Get all crypto configurations."""
    return ALL_CRYPTO

def get_primary_crypto() -> dict:
    """Get primary crypto configurations."""
    return PRIMARY_CRYPTO

def get_secondary_crypto() -> dict:
    """Get secondary crypto configurations."""
    return SECONDARY_CRYPTO

def get_stablecoins() -> dict:
    """Get stablecoin configurations."""
    return STABLECOINS

def get_stock_symbols() -> list:
    """Get list of all stock symbols."""
    return list(ALL_STOCKS.keys())

def get_crypto_symbols() -> list:
    """Get list of all crypto symbols."""
    return list(ALL_CRYPTO.keys())

def get_stock_by_symbol(symbol: str) -> Optional[dict]:
    """Get stock config by symbol."""
    return ALL_STOCKS.get(symbol.upper())

def get_crypto_by_symbol(symbol: str) -> Optional[dict]:
    """Get crypto config by symbol."""
    return ALL_CRYPTO.get(symbol.upper())
