const state = {
  watchlist: loadWatchlist(),
  selectedSymbol: null,
  timeframe: "1D",
  connection: null,
  detail: null,
  account: null,
  demo: null,
  chart: null,
  refreshTimers: [],
};

const els = {
  feedChip: document.getElementById("feed-mode-chip"),
  connectionCopy: document.getElementById("connection-copy"),
  marketStatusLabel: document.getElementById("market-status-label"),
  feedHealthCopy: document.getElementById("feed-health-copy"),
  feedProfileLabel: document.getElementById("feed-profile-label"),
  syncStamp: document.getElementById("sync-stamp"),
  watchlistCountLabel: document.getElementById("watchlist-count-label"),
  authToolbar: document.getElementById("auth-toolbar"),
  disconnectUpstoxBtn: document.getElementById("disconnect-upstox-btn"),
  authCopy: document.getElementById("auth-copy"),
  watchlistList: document.getElementById("watchlist-list"),
  indicesGrid: document.getElementById("indices-grid"),
  searchForm: document.getElementById("search-form"),
  searchInput: document.getElementById("symbol-search"),
  searchResults: document.getElementById("search-results"),
  selectedSymbol: document.getElementById("selected-symbol"),
  selectedSymbolNote: document.getElementById("selected-symbol-note"),
  availableMargin: document.getElementById("available-margin"),
  usedMarginNote: document.getElementById("used-margin-note"),
  holdingsPnl: document.getElementById("holdings-pnl"),
  holdingsValueNote: document.getElementById("holdings-value-note"),
  ordersCount: document.getElementById("orders-count"),
  ordersNote: document.getElementById("orders-note"),
  detailTitle: document.getElementById("detail-title"),
  detailPrice: document.getElementById("detail-price"),
  detailChange: document.getElementById("detail-change"),
  detailOpen: document.getElementById("detail-open"),
  detailHigh: document.getElementById("detail-high"),
  detailLow: document.getElementById("detail-low"),
  detailVolume: document.getElementById("detail-volume"),
  signalLabel: document.getElementById("signal-label"),
  signalBadge: document.getElementById("signal-badge"),
  biasScore: document.getElementById("bias-score"),
  biasFill: document.getElementById("bias-fill"),
  signalSummary: document.getElementById("signal-summary"),
  metricRsi: document.getElementById("metric-rsi"),
  metricMa20: document.getElementById("metric-ma20"),
  metricMa50: document.getElementById("metric-ma50"),
  metricMomentum: document.getElementById("metric-momentum"),
  metricVolatility: document.getElementById("metric-volatility"),
  metricRange: document.getElementById("metric-range"),
  holdingsBody: document.getElementById("holdings-body"),
  positionsBody: document.getElementById("positions-body"),
  ordersBody: document.getElementById("orders-body"),
  orderForm: document.getElementById("order-form"),
  orderSymbol: document.getElementById("order-symbol"),
  orderQty: document.getElementById("order-qty"),
  orderSide: document.getElementById("order-side"),
  orderProduct: document.getElementById("order-product"),
  orderType: document.getElementById("order-type"),
  orderPrice: document.getElementById("order-price"),
  orderNote: document.getElementById("order-note"),
  placeOrderBtn: document.getElementById("place-order-btn"),
  newsCopy: document.getElementById("news-copy"),
  newsList: document.getElementById("news-list"),
  refreshNewsBtn: document.getElementById("refresh-news-btn"),
  demoCopy: document.getElementById("demo-copy"),
  demoLoginForm: document.getElementById("demo-login-form"),
  demoUsername: document.getElementById("demo-username"),
  demoPassword: document.getElementById("demo-password"),
  demoLoginBtn: document.getElementById("demo-login-btn"),
  demoLogoutBtn: document.getElementById("demo-logout-btn"),
  walletCash: document.getElementById("wallet-cash"),
  walletInvested: document.getElementById("wallet-invested"),
  walletEquity: document.getElementById("wallet-equity"),
  walletRealized: document.getElementById("wallet-realized"),
  walletActivity: document.getElementById("wallet-activity"),
  toast: document.getElementById("toast"),
};


function loadWatchlist() {
  const saved = window.localStorage.getItem("stockmind-upstox-watchlist");
  if (!saved) {
    return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT"];
  }
  try {
    const parsed = JSON.parse(saved);
    if (Array.isArray(parsed) && parsed.length) {
      return parsed.slice(0, 14);
    }
  } catch (error) {
    console.warn("Could not parse saved watchlist.", error);
  }
  return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT"];
}


function saveWatchlist() {
  window.localStorage.setItem("stockmind-upstox-watchlist", JSON.stringify(state.watchlist));
}


function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}


function number(value, fractionDigits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: fractionDigits,
  }).format(Number(value));
}


function signedPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}%`;
}


function setText(node, value) {
  if (!node) {
    return;
  }
  node.textContent = value;
}


function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.remove("visible");
  }, 2800);
}


async function api(url, options = {}) {
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch (error) {
    data = {};
  }
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}


function toneClass(value) {
  const numeric = Number(value);
  if (numeric > 0) return "positive";
  if (numeric < 0) return "negative";
  return "neutral";
}


function stampNow() {
  setText(els.syncStamp, new Date().toLocaleTimeString("en-IN", { hour12: false }));
}


function redirectHint(redirectUri) {
  if (!redirectUri) {
    return "";
  }
  try {
    const redirectUrl = new URL(redirectUri);
    const redirectHost = redirectUrl.hostname;
    const currentHost = window.location.hostname;
    const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
    if (!currentHost || localHosts.has(currentHost) || !localHosts.has(redirectHost)) {
      return "";
    }
    return ` If you are opening this dashboard on another device, register and use ${window.location.origin}/upstox/callback as the Upstox redirect URI.`;
  } catch (error) {
    console.warn("Could not parse Upstox redirect URI.", error);
    return "";
  }
}


function relativeTime(value) {
  if (!value) {
    return "Waiting for update";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Waiting for update";
  }
  const diffMinutes = Math.round((Date.now() - parsed.getTime()) / 60000);
  if (diffMinutes <= 1) {
    return "Just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr ago`;
  }
  return parsed.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}


function formatStamp(value) {
  if (!value) {
    return "--";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function renderActivity(items) {
  els.walletActivity.innerHTML = "";
  if (!items?.length) {
    els.walletActivity.innerHTML = `<div class="empty-state">Demo activity will appear here after the first paper trade.</div>`;
    return;
  }

  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = "activity-item";
    row.innerHTML = `
      <div class="activity-meta">
        <strong>${item.title}</strong>
        <span>${relativeTime(item.timestamp)}</span>
      </div>
      <div class="activity-copy">${item.subtitle}</div>
    `;
    els.walletActivity.appendChild(row);
  });
}


function renderWallet(wallet) {
  const safeWallet = wallet || {};
  setText(els.walletCash, money(safeWallet.cash_balance));
  setText(els.walletInvested, money(safeWallet.invested_value));
  setText(els.walletEquity, money(safeWallet.total_equity));
  setText(els.walletRealized, money(safeWallet.realized_pnl));
  els.walletRealized.className = `wallet-value ${toneClass(safeWallet.realized_pnl)}`;
}


function setOrderAccess(connection) {
  const demoActive = state.demo?.logged_in;
  const hasFullAccess = connection?.auth_mode === "full";
  const canTrade = demoActive || hasFullAccess;
  const orderControls = els.orderForm.querySelectorAll("input, select, button");

  orderControls.forEach((control) => {
    control.disabled = !canTrade;
  });

  els.orderForm.classList.toggle("is-disabled", !canTrade);

  if (demoActive) {
    els.placeOrderBtn.textContent = "Submit demo order";
    els.orderNote.textContent = "Demo account is active. Orders are paper-traded using the live market quote or your demo limit price.";
    toggleLimitPrice();
    return;
  }

  if (hasFullAccess) {
    els.placeOrderBtn.textContent = "Submit order";
    els.orderNote.textContent = "Orders are sent using the active broker session. If Upstox rejects them, verify the registered static IP.";
    toggleLimitPrice();
    return;
  }

  els.orderPrice.disabled = true;
  els.placeOrderBtn.textContent = "Order placement locked";

  if (!connection?.configured) {
    els.orderNote.textContent = "Order API needs Upstox OAuth plus a registered static IP. Configure client ID, client secret, and redirect URI first.";
    return;
  }

  els.orderNote.textContent = connection?.auth_mode === "analytics"
    ? "Read-only feed is active. Use the demo login for paper trading, or connect a full Upstox trading token for live orders."
    : "No active trading token found. Use the demo account for paper trades, or reconnect Upstox after static IP setup.";
}


function renderDemoState(demo) {
  state.demo = demo;
  renderWallet(demo?.wallet);
  renderActivity(demo?.recent_activity || []);
  setText(els.demoCopy, demo?.message || "Demo account status is unavailable.");

  const loggedIn = Boolean(demo?.logged_in);
  els.demoUsername.disabled = loggedIn;
  els.demoPassword.disabled = loggedIn;
  els.demoLoginBtn.hidden = loggedIn;
  els.demoLogoutBtn.hidden = !loggedIn;

  if (!loggedIn) {
    els.demoPassword.value = "";
  }

  setOrderAccess(state.connection);
}


function renderAuthState(connection) {
  const mode = connection?.auth_mode || "none";
  const userName = connection?.user?.user_name || connection?.user?.user_id || "your Upstox account";
  const noteSuffix = redirectHint(connection?.redirect_uri);

  els.authToolbar.hidden = true;
  els.disconnectUpstoxBtn.hidden = true;
  els.disconnectUpstoxBtn.disabled = false;
  setOrderAccess(connection);

  if (mode === "full") {
    els.authToolbar.hidden = false;
    els.disconnectUpstoxBtn.hidden = false;
    els.authCopy.textContent = `Connected to ${userName}. Holdings, positions, margins, and orders are now available.${noteSuffix}`;
    return;
  }

  if (mode === "analytics") {
    els.authCopy.textContent = `Read-only market feed is active. To place API orders, use a full trading token and make sure requests originate from your registered static IP.${noteSuffix}`;
    return;
  }

  els.authCopy.textContent = connection?.configured
    ? `No active trading token found. Market data can run in read-only mode, but API orders need a fresh full token after static IP setup.${noteSuffix}`
    : "Upstox OAuth is not configured yet. Set UPSTOX_CLIENT_ID, UPSTOX_CLIENT_SECRET, and UPSTOX_REDIRECT_URI first.";
}


function renderConnection(connection, marketStatus) {
  state.connection = connection;
  renderAuthState(connection);
  const mode = connection?.auth_mode || "none";
  let feedLabel = "Feed offline";
  let profileLabel = connection?.configured ? "Connect required" : "Setup required";
  let copy = "Market feed is unavailable right now. Live prices will appear as soon as a valid session is detected.";
  let healthCopy = "Waiting for the next refresh cycle.";

  if (mode === "full") {
    feedLabel = "Live account feed";
    profileLabel = "Full access";
    copy = "Live prices, portfolio depth, and order flow are active across the dashboard.";
    healthCopy = "Quotes, holdings, positions, and orders are available.";
  } else if (mode === "analytics") {
    feedLabel = "Read-only live feed";
    profileLabel = "Market-only";
    copy = "Live prices and index movement are active across the dashboard.";
    healthCopy = "Quotes and market breadth are updating normally.";
  }

  els.feedChip.textContent = feedLabel;
  els.feedProfileLabel.textContent = profileLabel;
  els.connectionCopy.textContent = copy;
  els.feedHealthCopy.textContent = healthCopy;

  if (marketStatus?.status) {
    const marketLabel = marketStatus.status.replaceAll("_", " ");
    setText(els.marketStatusLabel, marketLabel);
    if (mode !== "none") {
      setText(els.feedHealthCopy, `Session state: ${marketLabel}.`);
    }
  } else {
    setText(els.marketStatusLabel, mode === "none" ? "Session required" : "Unavailable");
    if (mode === "none" && connection?.message) {
      setText(els.feedHealthCopy, connection.message);
    }
  }

  setText(els.watchlistCountLabel, `${state.watchlist.length} symbols`);
}


function renderNews(items) {
  els.newsList.innerHTML = "";
  if (!items?.length) {
    els.newsList.innerHTML = `<div class="empty-state">Live economics headlines will appear here as soon as the feed responds.</div>`;
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "news-item";
    card.innerHTML = `
      <div class="news-meta">
        <span>${item.source || "Live feed"}</span>
        <span>${relativeTime(item.published_at)}</span>
      </div>
      <a href="${item.link}" target="_blank" rel="noreferrer">${item.title}</a>
      <div class="news-summary">${item.summary || "Open the story to read the full economics update."}</div>
    `;
    els.newsList.appendChild(card);
  });
}


function renderIndices(indices) {
  els.indicesGrid.innerHTML = "";
  if (!indices.length) {
    els.indicesGrid.innerHTML = `<div class="empty-state">Live index data will appear here once the market snapshot is ready.</div>`;
    return;
  }

  indices.forEach((item) => {
    const card = document.createElement("article");
    card.className = "index-card";
    card.innerHTML = `
      <h3>${item.display_name}</h3>
      <strong>${money(item.last_price)}</strong>
      <span class="${toneClass(item.pct_change)}">${signedPct(item.pct_change)}</span>
    `;
    els.indicesGrid.appendChild(card);
  });
}


function renderWatchlist(items) {
  els.watchlistList.innerHTML = "";
  setText(els.watchlistCountLabel, `${items.length} symbols`);
  if (!items.length) {
    els.watchlistList.innerHTML = `<div class="empty-state">No live quotes are available right now.</div>`;
    return;
  }

  if (!state.selectedSymbol) {
    state.selectedSymbol = items[0].symbol;
  }

  items.forEach((item) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `watch-row ${item.symbol === state.selectedSymbol ? "is-active" : ""}`;
    row.innerHTML = `
      <div class="watch-top">
        <div>
          <div class="watch-symbol">${item.symbol}</div>
          <div class="watch-name">${item.display_name}</div>
        </div>
        <div>
          <div class="watch-price">${money(item.last_price)}</div>
          <div class="watch-change ${toneClass(item.pct_change)}">${signedPct(item.pct_change)}</div>
        </div>
      </div>
    `;
    row.addEventListener("click", () => {
      state.selectedSymbol = item.symbol;
      els.orderSymbol.value = item.symbol;
      refreshDetail();
      renderWatchlist(items);
    });
    els.watchlistList.appendChild(row);
  });
}


function renderSummary(account) {
  const selected = state.detail?.quote;
  setText(els.selectedSymbol, state.selectedSymbol || "--");
  setText(
    els.selectedSymbolNote,
    selected ? `${money(selected.last_price)} | ${signedPct(selected.pct_change)}` : "Choose a symbol from the watchlist."
  );

  if (account?.ok) {
    setText(els.availableMargin, money(account.summary.available_margin));
    setText(els.usedMarginNote, account.mode === "demo"
      ? `Demo invested value ${money(account.summary.used_margin)}`
      : `Used margin ${money(account.summary.used_margin)}`
    );
    setText(els.holdingsPnl, money(account.summary.holdings_pnl));
    els.holdingsPnl.className = `stat-value ${toneClass(account.summary.holdings_pnl)}`;
    setText(
      els.holdingsValueNote,
      account.mode === "demo"
        ? `Demo equity ${money(account.summary.total_equity)}`
        : `Holdings value ${money(account.summary.holdings_value)}`
    );
    setText(els.ordersCount, String(account.summary.orders_today));
    setText(
      els.ordersNote,
      account.mode === "demo"
        ? `Demo account: ${account.profile?.user_name || "Paper trader"}`
        : account.profile?.user_name ? `Account: ${account.profile.user_name}` : "Broker account synced."
    );
  } else {
    setText(els.availableMargin, "--");
    setText(els.usedMarginNote, "Margin appears when broker account or demo wallet sync is active.");
    setText(els.holdingsPnl, "--");
    els.holdingsPnl.className = "stat-value";
    setText(els.holdingsValueNote, account?.error || "Portfolio value stream appears here.");
    setText(els.ordersCount, "--");
    setText(els.ordersNote, "Orders sync when an account session is active.");
  }
}


function renderDetail(detail) {
  if (!detail?.ok) {
    setText(els.detailTitle, "Select a symbol");
    setText(els.detailPrice, "--");
    setText(els.detailChange, detail?.error || "Waiting for live data");
    els.detailChange.className = "quote-change";
    setText(els.signalLabel, "No symbol selected");
    setText(els.signalBadge, "--");
    els.signalBadge.className = "bias-badge";
    setText(els.signalSummary, "Select a symbol to load live history and the model view.");
    setText(els.detailOpen, "--");
    setText(els.detailHigh, "--");
    setText(els.detailLow, "--");
    setText(els.detailVolume, "--");
    return;
  }

  const quote = detail.quote;
  const signal = detail.signal;

  setText(els.detailTitle, detail.display_name);
  setText(els.detailPrice, money(quote.last_price));
  setText(els.detailChange, `${money(quote.net_change)} | ${signedPct(quote.pct_change)}`);
  els.detailChange.className = `quote-change ${toneClass(quote.pct_change)}`;
  setText(els.detailOpen, money(quote.open));
  setText(els.detailHigh, money(quote.high));
  setText(els.detailLow, money(quote.low));
  setText(els.detailVolume, number(quote.volume, 0));

  setText(els.signalLabel, `${detail.symbol} signal`);
  setText(els.signalBadge, signal.signal);
  els.signalBadge.className = `bias-badge ${toneClass(signal.signal === "BUY" ? 1 : signal.signal === "SELL" ? -1 : 0)}`;
  setText(els.biasScore, String(signal.bias_score));
  els.biasFill.style.width = `${signal.bias_score}%`;
  setText(els.signalSummary, signal.summary);
  setText(els.metricRsi, number(signal.rsi));
  setText(els.metricMa20, money(signal.ma20));
  setText(els.metricMa50, money(signal.ma50));
  setText(els.metricMomentum, signedPct(signal.momentum_20d));
  setText(els.metricVolatility, signedPct(signal.volatility_20d));
  setText(els.metricRange, `${money(signal.support)} / ${money(signal.resistance)}`);

  els.orderSymbol.value = detail.symbol;
  drawChart(detail.history, detail.symbol);
}


function drawChart(history, symbol) {
  const ctx = document.getElementById("price-chart").getContext("2d");
  const labels = history.map((item) => {
    const date = new Date(item.ts);
    if (state.timeframe === "1D") {
      return date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  });
  const values = history.map((item) => item.close);

  if (state.chart) {
    state.chart.destroy();
  }

  state.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: symbol,
          data: values,
          borderColor: "#11795a",
          backgroundColor: "rgba(17, 121, 90, 0.12)",
          borderWidth: 2.4,
          pointRadius: 0,
          tension: 0.28,
          fill: true,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          intersect: false,
          mode: "index",
          callbacks: {
            label(context) {
              return money(context.parsed.y);
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#687468", maxRotation: 0 },
          grid: { display: false },
        },
        y: {
          ticks: {
            color: "#687468",
            callback(value) {
              return number(value, 0);
            },
          },
          grid: { color: "rgba(104, 116, 104, 0.12)" },
        },
      },
    },
  });
}


function renderTableRows(target, rows, mapper, emptyText, colspan = 7) {
  target.innerHTML = "";
  if (!rows.length) {
    target.innerHTML = `<tr><td colspan="${colspan}" class="empty-state">${emptyText}</td></tr>`;
    return;
  }

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = mapper(row);
    target.appendChild(tr);
  });
}


function renderAccount(account) {
  if (!account?.ok) {
    renderTableRows(
      els.holdingsBody,
      [],
      () => "",
      account?.error || "Holdings are unavailable for the current session.",
      6
    );
    renderTableRows(
      els.positionsBody,
      [],
      () => "",
      account?.error || "Positions are unavailable for the current session.",
      6
    );
    renderTableRows(
      els.ordersBody,
      [],
      () => "",
      account?.error || "Orders are unavailable for the current session.",
      7
    );
    els.orderNote.textContent = "Trading becomes available when an account or demo session is active.";
    return;
  }

  renderTableRows(
    els.holdingsBody,
    account.holdings,
    (item) => `
      <td><div class="symbol-cell">${item.symbol}</div><div class="subtle">${item.name || item.exchange}</div></td>
      <td>${number(item.quantity, 0)}</td>
      <td>${money(item.average_price)}</td>
      <td>${money(item.last_price)}</td>
      <td>${money(item.current_value)}</td>
      <td class="${toneClass(item.pnl)}">${money(item.pnl)}</td>
    `,
    account.mode === "demo" ? "No demo holdings yet. Use delivery or MTF paper trades to build the wallet." : "No holdings were returned by the broker.",
    6
  );

  renderTableRows(
    els.positionsBody,
    account.positions,
    (item) => `
      <td><div class="symbol-cell">${item.symbol}</div><div class="subtle">${item.exchange}</div></td>
      <td>${item.product}</td>
      <td>${number(item.quantity, 0)}</td>
      <td>${money(item.average_price)}</td>
      <td>${money(item.last_price)}</td>
      <td class="${toneClass(item.pnl)}">${money(item.pnl)}</td>
    `,
    account.mode === "demo" ? "No demo intraday positions are open right now." : "No open positions were returned by the broker.",
    6
  );

  renderTableRows(
    els.ordersBody,
    account.orders,
    (item) => `
      <td>${formatStamp(item.order_timestamp)}</td>
      <td><div class="symbol-cell">${item.symbol}</div><div class="subtle">${item.exchange}</div></td>
      <td>${item.transaction_type}</td>
      <td>${item.order_type}</td>
      <td>${number(item.quantity, 0)}</td>
      <td><div class="symbol-cell">${item.status}</div><div class="subtle">${item.status_message || ""}</div></td>
      <td>${money(item.average_price)}</td>
    `,
    account.mode === "demo" ? "No demo orders have been placed today." : "No orders returned for the current day.",
    7
  );

  if (account.mode === "demo") {
    els.orderNote.textContent = "Demo account is active. These fills update the local wallet only.";
  } else {
    els.orderNote.textContent = "Orders are sent using the active broker session.";
  }
}


async function refreshSnapshot() {
  const query = encodeURIComponent(state.watchlist.join(","));
  const snapshot = await api(`/api/market/snapshot?symbols=${query}`);
  renderConnection(snapshot.connection, snapshot.market_status);
  renderWatchlist(snapshot.watchlist || []);
  renderIndices(snapshot.indices || []);
  stampNow();

  if (!snapshot.watchlist?.length) {
    state.selectedSymbol = null;
    state.detail = null;
    renderDetail({
      ok: false,
      error: snapshot.error || "Connect Upstox or add an analytics token to load live quotes.",
    });
    return;
  }

  if (!state.selectedSymbol || !snapshot.watchlist.some((item) => item.symbol === state.selectedSymbol)) {
    state.selectedSymbol = snapshot.watchlist[0].symbol;
  }
}


async function refreshDetail() {
  if (!state.selectedSymbol) {
    return;
  }
  try {
    const detail = await api(`/api/market/detail/${encodeURIComponent(state.selectedSymbol)}?tf=${state.timeframe}`);
    state.detail = detail;
    renderDetail(detail);
    renderSummary(state.account);
  } catch (error) {
    state.detail = null;
    renderDetail({ ok: false, error: error.message });
    showToast(error.message);
  }
}


async function refreshAccount() {
  try {
    const overview = await api("/api/account/overview");
    state.account = overview;
  } catch (error) {
    state.account = { ok: false, error: error.message };
  }
  renderAccount(state.account);
  renderSummary(state.account);
  setOrderAccess(state.connection);
}


async function refreshDemo() {
  try {
    const demo = await api("/api/demo/status");
    renderDemoState(demo);
  } catch (error) {
    renderDemoState({
      logged_in: false,
      wallet: null,
      recent_activity: [],
      message: error.message,
    });
  }
}


async function refreshNews(forceRefresh = false) {
  const suffix = forceRefresh ? "?refresh=1" : "";
  try {
    const data = await api(`/api/news/economy${suffix}`);
    setText(els.newsCopy, "Streaming the latest economy and market-moving headlines.");
    renderNews(data.items || []);
  } catch (error) {
    setText(els.newsCopy, error.message);
    renderNews([]);
  }
}


async function refreshAll() {
  try {
    await Promise.all([refreshSnapshot(), refreshDemo(), refreshNews()]);
    await Promise.all([refreshDetail(), refreshAccount()]);
  } catch (error) {
    showToast(error.message);
  }
}


async function searchSymbol(event) {
  event.preventDefault();
  const query = els.searchInput.value.trim();
  els.searchResults.innerHTML = "";
  if (!query) {
    return;
  }

  try {
    const data = await api(`/api/market/search?q=${encodeURIComponent(query)}`);
    if (!data.results.length) {
      els.searchResults.innerHTML = `<div class="empty-state">No matching NSE/BSE equity symbol found.</div>`;
      return;
    }

    data.results.forEach((item) => {
      const row = document.createElement("div");
      row.className = "search-result";
      row.innerHTML = `
        <div>
          <div class="symbol-cell">${item.symbol}</div>
          <div class="subtle">${item.name || item.exchange}</div>
        </div>
        <button type="button">Add</button>
      `;
      row.querySelector("button").addEventListener("click", async () => {
        if (!state.watchlist.includes(item.symbol)) {
          state.watchlist.unshift(item.symbol);
          state.watchlist = state.watchlist.slice(0, 14);
          saveWatchlist();
        }
        state.selectedSymbol = item.symbol;
        els.searchInput.value = "";
        els.searchResults.innerHTML = "";
        await refreshAll();
        showToast(`${item.symbol} added to the watchlist.`);
      });
      els.searchResults.appendChild(row);
    });
  } catch (error) {
    els.searchResults.innerHTML = `<div class="empty-state">${error.message}</div>`;
  }
}


async function submitOrder(event) {
  event.preventDefault();
  if (!state.demo?.logged_in && state.connection?.auth_mode !== "full") {
    showToast("Order placement needs either the demo account or a fresh full Upstox token.");
    return;
  }

  const payload = {
    symbol: els.orderSymbol.value.trim().toUpperCase(),
    quantity: Number(els.orderQty.value),
    transaction_type: els.orderSide.value,
    product: els.orderProduct.value,
    order_type: els.orderType.value,
    price: Number(els.orderPrice.value || 0),
  };

  try {
    const result = await api("/api/account/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(result.message);
    await Promise.all([refreshAccount(), refreshDemo()]);
  } catch (error) {
    showToast(error.message);
  }
}


async function submitDemoLogin(event) {
  event.preventDefault();
  const username = els.demoUsername.value.trim();
  const password = els.demoPassword.value;

  if (!username || !password) {
    showToast("Enter the demo username and password.");
    return;
  }

  els.demoLoginBtn.disabled = true;
  try {
    await api("/api/demo/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    showToast("Demo account logged in.");
    await Promise.all([refreshDemo(), refreshAccount()]);
  } catch (error) {
    showToast(error.message);
  } finally {
    els.demoLoginBtn.disabled = false;
  }
}


async function logoutDemo() {
  els.demoLogoutBtn.disabled = true;
  try {
    await api("/api/demo/logout", { method: "POST" });
    showToast("Demo account logged out.");
    await Promise.all([refreshDemo(), refreshAccount()]);
  } catch (error) {
    showToast(error.message);
  } finally {
    els.demoLogoutBtn.disabled = false;
  }
}


async function disconnectUpstox() {
  const confirmed = window.confirm("Disconnect the current Upstox session?");
  if (!confirmed) {
    return;
  }

  els.disconnectUpstoxBtn.disabled = true;
  try {
    await api("/api/upstox/disconnect", { method: "POST" });
    showToast("Upstox session disconnected.");
    state.selectedSymbol = null;
    await refreshAll();
  } catch (error) {
    showToast(error.message);
  } finally {
    els.disconnectUpstoxBtn.disabled = false;
  }
}


function toggleLimitPrice() {
  const needsPrice = els.orderType.value === "LIMIT";
  const canUsePrice = state.demo?.logged_in || state.connection?.auth_mode === "full";
  els.orderPrice.disabled = !needsPrice || !canUsePrice;
  if (!needsPrice) {
    els.orderPrice.value = "";
  }
}


function bindEvents() {
  els.disconnectUpstoxBtn.addEventListener("click", disconnectUpstox);
  els.searchForm.addEventListener("submit", searchSymbol);
  els.orderForm.addEventListener("submit", submitOrder);
  els.orderType.addEventListener("change", toggleLimitPrice);
  els.demoLoginForm.addEventListener("submit", submitDemoLogin);
  els.demoLogoutBtn.addEventListener("click", logoutDemo);
  els.refreshNewsBtn.addEventListener("click", async () => {
    els.refreshNewsBtn.disabled = true;
    try {
      await refreshNews(true);
      showToast("Economics headlines refreshed.");
    } finally {
      els.refreshNewsBtn.disabled = false;
    }
  });

  document.querySelectorAll(".timeframe-button").forEach((button) => {
    button.addEventListener("click", async () => {
      document.querySelectorAll(".timeframe-button").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      state.timeframe = button.dataset.tf;
      await refreshDetail();
    });
  });

  window.addEventListener("message", async (event) => {
    if (event.data?.type !== "upstox-auth") {
      return;
    }
    showToast(event.data.message || (event.data.success ? "Broker session updated." : "Broker session update failed."));
    await refreshAll();
  });
}


function startAutoRefresh() {
  state.refreshTimers.forEach((timer) => window.clearInterval(timer));
  state.refreshTimers = [
    window.setInterval(refreshSnapshot, 20000),
    window.setInterval(refreshDetail, 30000),
    window.setInterval(refreshAccount, 45000),
    window.setInterval(refreshDemo, 45000),
    window.setInterval(refreshNews, 300000),
  ];
}


async function boot() {
  bindEvents();
  toggleLimitPrice();
  await refreshAll();
  startAutoRefresh();
}


boot();
