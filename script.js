(() => {
    const API_KEY = 'GC3BE0ZFAMH7Q25I';
    const API_BASE = 'https://www.alphavantage.co/query';

    const els = {
        tickerInput: document.getElementById('ticker-input'),
        loadBtn: document.getElementById('load-btn'),
        status: document.getElementById('status'),
        game: document.getElementById('game'),
        symbol: document.getElementById('symbol'),
        currentDate: document.getElementById('current-date'),
        score: document.getElementById('score'),
        feedback: document.getElementById('feedback'),
        guessUp: document.getElementById('guess-up'),
        guessDown: document.getElementById('guess-down'),
        endGame: document.getElementById('end-game'),
        chartCanvas: document.getElementById('chart')
    };

    /**
     * Game state
     */
    let state = {
        symbol: '',
        tz: 'US/Eastern',
        seriesByDate: new Map(), // yyyy-mm-dd -> number (close)
        orderedDates: [], // sorted ascending
        startIndex: -1, // index of start date in orderedDates
        currentIndex: -1, // index of latest revealed date
        score: 0,
        chart: null
    };

    function setStatus(text, isError = false) {
        els.status.textContent = text || '';
        els.status.style.color = isError ? '#ef4444' : '';
    }

    function setFeedback(text, isError = false) {
        els.feedback.textContent = text || '';
        els.feedback.style.color = isError ? '#ef4444' : '';
    }

    function fmtDate(d) {
        return d.toISOString().slice(0, 10);
    }

    function isWeekend(date) {
        const day = date.getUTCDay();
        return day === 0 || day === 6;
    }

    function pickRandomStartDate(validDatesAsc) {
        // choose a date between [today-100, today-7], must be present in validDatesAsc
        const today = new Date();
        const min = new Date(today);
        min.setUTCDate(today.getUTCDate() - 100);
        const max = new Date(today);
        max.setUTCDate(today.getUTCDate() - 7);

        // Filter validDatesAsc within [min,max]
        const inRange = validDatesAsc.filter(ds => {
            const d = new Date(ds + 'T00:00:00Z');
            return d >= new Date(fmtDate(min) + 'T00:00:00Z') && d <= new Date(fmtDate(max) + 'T00:00:00Z');
        });

        if (inRange.length === 0) return null;

        // Randomly select an element that is a weekday (market day). Data set already market days.
        const idx = Math.floor(Math.random() * inRange.length);
        return inRange[idx];
    }

    async function fetchDailyAdjusted(symbol) {
        const url = `${API_BASE}?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${encodeURIComponent(symbol)}&apikey=${API_KEY}&outputsize=full`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`Network error ${resp.status}`);
        const data = await resp.json();
        if (data['Error Message']) throw new Error('Ticker not found');
        if (data['Note']) throw new Error('API rate limit reached. Please wait a minute.');
        const meta = data['Meta Data'];
        const series = data['Time Series (Daily)'];
        if (!meta || !series) throw new Error('Unexpected API response');
        return { meta, series };
    }

    function buildSeriesMap(seriesObj) {
        const map = new Map();
        for (const [dateStr, ohlc] of Object.entries(seriesObj)) {
            // use adjusted close or close? We'll use close ("4. close")
            const close = Number(ohlc['4. close']);
            if (!Number.isFinite(close)) continue;
            map.set(dateStr, close);
        }
        const ordered = Array.from(map.keys()).sort((a, b) => a.localeCompare(b));
        return { map, ordered };
    }

    function initChart(labels, data) {
        if (state.chart) {
            state.chart.destroy();
            state.chart = null;
        }
        const ctx = els.chartCanvas.getContext('2d');
        state.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: `${state.symbol} Close`,
                    data,
                    borderColor: '#7c88ff',
                    backgroundColor: 'rgba(124,136,255,0.15)',
                    tension: 0.2,
                    pointRadius: 3,
                    pointBackgroundColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#9aa3b2' }, grid: { color: 'rgba(255,255,255,0.08)' } },
                    y: { ticks: { color: '#9aa3b2' }, grid: { color: 'rgba(255,255,255,0.08)' } }
                },
                plugins: {
                    legend: { labels: { color: '#e6e8f0' } },
                    tooltip: { callbacks: { label: (ctx) => `Close: ${ctx.parsed.y}` } }
                }
            }
        });
    }

    function revealThroughIndex(targetIndex) {
        const labels = state.orderedDates.slice(state.startIndex - 7, targetIndex + 1);
        const data = labels.map(d => state.seriesByDate.get(d));
        initChart(labels, data);
        els.currentDate.textContent = labels[labels.length - 1];
    }

    async function startGameForSymbol(symbolInput) {
        setFeedback('');
        setStatus('Loading data...');
        disableControls(true);
        try {
            const symbol = symbolInput.trim().toUpperCase();
            if (!symbol) throw new Error('Please enter a stock ticker symbol.');
            const { meta, series } = await fetchDailyAdjusted(symbol);
            state.symbol = symbol;
            state.tz = meta['5. Time Zone'] || 'US/Eastern';
            const { map, ordered } = buildSeriesMap(series);

            // pick start date
            const startDateStr = pickRandomStartDate(ordered);
            if (!startDateStr) throw new Error('Not enough recent history to pick a start date.');
            const startIdx = ordered.indexOf(startDateStr);
            if (startIdx < 7) throw new Error('Insufficient prior days for chart. Try another symbol.');

            state.seriesByDate = map;
            state.orderedDates = ordered;
            state.startIndex = startIdx;
            state.currentIndex = startIdx; // start date is the latest revealed at first
            state.score = 0;
            els.score.textContent = '0';
            els.symbol.textContent = state.symbol;
            els.game.hidden = false;

            // show prior 7 days up to start date
            revealThroughIndex(state.currentIndex);
            setStatus('Loaded. Make your prediction for the next day.');
        } catch (err) {
            console.error(err);
            setStatus(err.message || 'Failed to load', true);
            els.game.hidden = true;
        } finally {
            disableControls(false);
        }
    }

    function disableControls(disabled) {
        els.loadBtn.disabled = disabled;
        els.tickerInput.disabled = disabled;
        els.guessUp.disabled = disabled;
        els.guessDown.disabled = disabled;
        els.endGame.disabled = disabled;
    }

    function nextTradableIndex(fromIndex) {
        // Data only contains trading days; the next index is simply +1 if exists
        if (fromIndex + 1 < state.orderedDates.length) return fromIndex + 1;
        return -1;
    }

    function handleGuess(isUp) {
        if (state.currentIndex < 0) return;
        const nextIdx = nextTradableIndex(state.currentIndex);
        if (nextIdx === -1) {
            setFeedback('No more data to reveal. Game over.');
            return;
        }
        const todayPrice = state.seriesByDate.get(state.orderedDates[state.currentIndex]);
        const nextPrice = state.seriesByDate.get(state.orderedDates[nextIdx]);
        const wentUp = nextPrice > todayPrice;
        const correct = isUp === wentUp;
        if (correct) state.score += 1;
        els.score.textContent = String(state.score);
        setFeedback(correct ? 'Correct!' : 'Wrong.');

        // reveal next day and update chart
        state.currentIndex = nextIdx;
        revealThroughIndex(state.currentIndex);
    }

    els.loadBtn.addEventListener('click', () => startGameForSymbol(els.tickerInput.value));
    els.tickerInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') startGameForSymbol(els.tickerInput.value);
    });
    els.guessUp.addEventListener('click', () => handleGuess(true));
    els.guessDown.addEventListener('click', () => handleGuess(false));
    els.endGame.addEventListener('click', () => {
        setFeedback('Game ended. You can enter another symbol to play again.');
    });
})();

