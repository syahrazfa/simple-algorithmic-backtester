# Simple Algorithmic Backtester

<a id="readme-top"></a>

[![LinkedIn][linkedin-shield]][linkedin-url]

<div align="center">
</div>


> Note that this is my first ever algorithmic backtester

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#overview">Overview</a>
      <a href="strategy-logic">Strategy Logic</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- OVERVIEW -->

## Overview

<p>A crypto backtesting engine that fetches OHLCV candles from Binance, stores them locally, and runs a layered long/short strategy combining SMA (20/50/200), RSI, Bollinger Bands, and Volume Spread Analysis (VSA). VSA is additionally visualized as a 3D vector space (spread, volume, close location) to inspect effort-vs-result dynamics per bar.</p> </br>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- STRATEGY LOGIC -->

## Strategy Logic


<p>The strategy is built as four layers, each narrowing down the previous one:</p>
<ol>
  <li>Regime (SMA 50/200) — persistent trend state. Golden cross = long bias, death cross = short bias.</li>
  <li>Trigger (SMA 20/50 cross) — the actual entry event within the current regime.</li>
  <li>Timing filter (RSI + Bollinger Bands) — vetoes entries that are chasing an already-overbought/oversold move.</li>
  <li>Conviction (VSA momentum) — requires volume/effort to agree with the trade direction before firing.</li>
</ol>
<p>Positions exit on a regime flip (the SMA 50/200 relationship reversing against the open position).</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- BUILT WITH -->
## Built With

* [![Python][python]][python-url]</li>
* [![SQLite][sqlite]][sqlite-url]</li>


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started
<b>Prerequisites :</b>
<ul>
  <li>Python 3.11</li>
  <li>pip</li>
</ul>

<b>Installation</b>
1. Clone Repo
```
   git clone https://github.com/your-username/simple-sma-crypto-strategy.git
```
2. Install Dependency
```
   pip install -r requirements.txt
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE -->
## Usage

Fetch and store historical candles, then run the backtest:

```
python main.py       # fetches/updates OHLCV data into data/data.db
python backtest.py   # runs the layered strategy and prints performance stats
```

<!-- LIMITATION-->
* No transaction costs or slippage modeled yet.
* No out-of-sample validation — results reflect the same window the strategy was designed against.
* No max drawdown tracking yet (only ending portfolio value).
* Single position at a time per symbol; no portfolio-level capital allocation across concurrent positions.

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Syahraz Fiqar Alamsyah - [@junsiee_](https://twitter.com/junsiee_) - syahrazfa@gmail.com

Project Link: [https://github.com/syahrazfa/simple-algorithmic-backtester](https://github.com/syahrazfa/simple-algorithmic-backtester)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- URL -->
[linkedin-shield]: https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white
[linkedin-url]: ---
[python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[python-url]: https://www.python.org/
[sqlite]: https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white
[sqlite-url]: https://docs.python.org/3/library/sqlite3.html
