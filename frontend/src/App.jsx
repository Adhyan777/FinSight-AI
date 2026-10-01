const API_BASE_URL = "https://finsight-ai-2inl.onrender.com";

import { useEffect, useMemo, useState } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import './App.css'

function App() {
  const [analytics, setAnalytics] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [forecast, setForecast] = useState(null)
  const [clusters, setClusters] = useState(null)
  const [transactions, setTransactions] = useState([])

  const [error, setError] = useState('')

  const [question, setQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState('')

  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')

  const [fileInputKey, setFileInputKey] = useState(0)

  // Transaction filters
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [sortBy, setSortBy] = useState('date-desc')

  const loadDashboardData = () => {
    setError('')

    fetch('http://127.0.0.1:5000/api/analytics')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => setAnalytics(data))
      .catch(() =>
        setError('Unable to connect to the FinSight AI backend.')
      )

    fetch('http://127.0.0.1:5000/api/anomalies')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => setAnomalies(data))
      .catch(() => console.log('Unable to load anomaly data.'))

    fetch('http://127.0.0.1:5000/api/forecast')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => setForecast(data))
      .catch(() => console.log('Unable to load forecast data.'))

    fetch('http://127.0.0.1:5000/api/clusters')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => setClusters(data))
      .catch(() => console.log('Unable to load clustering data.'))

    fetch('http://127.0.0.1:5000/api/transactions')
      .then((response) => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then((data) => setTransactions(data))
      .catch(() => console.log('Unable to load transactions.'))
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const handleUpload = async (event) => {
    const file = event.target.files[0]

    if (!file) return

    setUploading(true)
    setUploadMessage('')
    setUploadError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(
        'http://127.0.0.1:5000/api/upload',
        {
          method: 'POST',
          body: formData,
        }
      )

      const data = await response.json()

      if (!response.ok) {
        if (data.missing_columns) {
          throw new Error(
            `Missing columns: ${data.missing_columns.join(', ')}`
          )
        }

        throw new Error(
          data.error || 'Unable to upload CSV file.'
        )
      }

      setUploadMessage(
        `Successfully uploaded ${data.transactions} transactions.`
      )

      loadDashboardData()
    } catch (error) {
      setUploadError(
        error.message || 'Unable to upload CSV file.'
      )
    } finally {
      setUploading(false)
      setFileInputKey((value) => value + 1)
    }
  }

  const askFinSight = async () => {
    if (!question.trim()) {
      setAiError('Please enter a question.')
      return
    }

    setAiLoading(true)
    setAiError('')
    setAiAnswer('')

    try {
      const response = await fetch(
        'http://127.0.0.1:5000/api/ask',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: question.trim(),
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Unable to generate AI response.'
        )
      }

      setAiAnswer(data.answer)
    } catch (error) {
      setAiError(
        error.message ||
          'Unable to connect to the FinSight AI assistant.'
      )
    } finally {
      setAiLoading(false)
    }
  }

  const handleQuestionKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      askFinSight()
    }
  }

  // ==========================================================
  // TRANSACTION FILTERING AND SORTING
  // ==========================================================

  const categories = useMemo(() => {
    return [
      ...new Set(
        transactions.map(
          (transaction) => transaction.category
        )
      ),
    ].sort()
  }, [transactions])

  const filteredTransactions = useMemo(() => {
    let result = [...transactions]

    // Search
    if (searchTerm.trim()) {
      const search = searchTerm
        .toLowerCase()
        .trim()

      result = result.filter((transaction) =>
        transaction.description
          .toLowerCase()
          .includes(search)
      )
    }

    // Category filter
    if (categoryFilter !== 'all') {
      result = result.filter(
        (transaction) =>
          transaction.category === categoryFilter
      )
    }

    // Type filter
    if (typeFilter !== 'all') {
      result = result.filter(
        (transaction) =>
          transaction.type === typeFilter
      )
    }

    // Sorting
    result.sort((a, b) => {
      if (sortBy === 'date-desc') {
        return b.date.localeCompare(a.date)
      }

      if (sortBy === 'date-asc') {
        return a.date.localeCompare(b.date)
      }

      if (sortBy === 'amount-desc') {
        return b.amount - a.amount
      }

      if (sortBy === 'amount-asc') {
        return a.amount - b.amount
      }

      return 0
    })

    return result
  }, [
    transactions,
    searchTerm,
    categoryFilter,
    typeFilter,
    sortBy,
  ])

  if (error) {
    return (
      <div className="app">
        <nav className="navbar">
          <div className="logo">FinSight AI</div>

          <div className="nav-links">
            <a href="#dashboard">Dashboard</a>
            <a href="#analytics">Analytics</a>
            <a href="#transactions">Transactions</a>
            <a href="#insights">AI Insights</a>
            <a href="#ask-ai">Ask AI</a>
          </div>
        </nav>

        <main>
          <section className="hero" id="dashboard">
            <div>
              <p className="eyebrow">
                PERSONAL FINANCE INTELLIGENCE
              </p>

              <h1>
                Understand your money.
                <br />
                Make better decisions.
              </h1>

              <p className="hero-text">
                FinSight AI transforms your financial data into
                clear analytics, insights, and predictions.
              </p>

              <button
                type="button"
                onClick={() =>
                  document
                    .getElementById('csv-upload')
                    .click()
                }
              >
                Upload Transactions
              </button>

              <input
                key={fileInputKey}
                id="csv-upload"
                type="file"
                accept=".csv"
                onChange={handleUpload}
                style={{ display: 'none' }}
              />

              <p>{error}</p>
            </div>
          </section>
        </main>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="app">
        <nav className="navbar">
          <div className="logo">FinSight AI</div>
        </nav>

        <main>
          <section className="hero">
            <div>
              <p className="eyebrow">
                PERSONAL FINANCE INTELLIGENCE
              </p>

              <h1>
                Loading your financial data...
              </h1>
            </div>
          </section>
        </main>
      </div>
    )
  }

  const monthlySpendingData = Object.entries(
    analytics.monthly_expenses
  ).map(([month, amount]) => ({
    month: month.substring(5),
    expenses: amount,
    income: analytics.total_income / 6,
  }))

  const categorySpendingData = Object.entries(
    analytics.category_expenses
  ).map(([category, amount]) => ({
    category,
    amount,
  }))

  const clusterChartData =
    clusters?.summary.map((cluster) => ({
      cluster: `Cluster ${cluster.cluster}`,
      average: cluster.mean,
      count: cluster.count,
    })) || []

  return (
    <div className="app">

      {/* =====================================================
          NAVBAR
      ===================================================== */}

      <nav className="navbar">
        <div className="logo">FinSight AI</div>

        <div className="nav-links">
          <a href="#dashboard">Dashboard</a>
          <a href="#analytics">Analytics</a>
          <a href="#transactions">Transactions</a>
          <a href="#insights">AI Insights</a>
          <a href="#ask-ai">Ask AI</a>
        </div>
      </nav>


      <main>

        {/* ===================================================
            HERO
        =================================================== */}

        <section className="hero" id="dashboard">

          <div>

            <p className="eyebrow">
              PERSONAL FINANCE INTELLIGENCE
            </p>

            <h1>
              Understand your money.
              <br />
              Make better decisions.
            </h1>

            <p className="hero-text">
              FinSight AI transforms your financial data into
              clear analytics, insights, and predictions.
            </p>

            <button
              type="button"
              onClick={() =>
                document
                  .getElementById('csv-upload')
                  .click()
              }
              disabled={uploading}
            >
              {uploading
                ? 'Uploading...'
                : 'Upload Transactions'}
            </button>

            <input
              key={fileInputKey}
              id="csv-upload"
              type="file"
              accept=".csv"
              onChange={handleUpload}
              style={{ display: 'none' }}
            />

            {uploadMessage && (
              <p>{uploadMessage}</p>
            )}

            {uploadError && (
              <p>{uploadError}</p>
            )}

          </div>

        </section>


        {/* ===================================================
            OVERVIEW
        =================================================== */}

        <section className="overview">

          <p className="eyebrow">
            OVERVIEW
          </p>

          <h2>
            Your financial picture.
          </h2>

          <div className="stats-grid">

            <div className="stat-card">
              <span>Total Income</span>

              <h3>
                ₹
                {analytics.total_income.toLocaleString(
                  'en-IN'
                )}
              </h3>
            </div>

            <div className="stat-card">
              <span>Total Expenses</span>

              <h3>
                ₹
                {analytics.total_expenses.toLocaleString(
                  'en-IN'
                )}
              </h3>
            </div>

            <div className="stat-card">
              <span>Savings</span>

              <h3>
                ₹
                {analytics.total_savings.toLocaleString(
                  'en-IN'
                )}
              </h3>
            </div>

            <div className="stat-card">
              <span>Savings Rate</span>

              <h3>
                {analytics.savings_rate}%
              </h3>
            </div>

          </div>

        </section>


        {/* ===================================================
            ANALYTICS
        =================================================== */}

        <section
          className="analytics"
          id="analytics"
        >

          <p className="eyebrow">
            ANALYTICS
          </p>

          <h2>
            See where your money goes.
          </h2>


          <div className="analytics-grid">

            <div className="chart-placeholder">

              <h3>
                Monthly Spending
              </h3>

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <LineChart
                  data={monthlySpendingData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="month"
                  />

                  <YAxis />

                  <Tooltip
                    formatter={(value) =>
                      `₹${Number(
                        value
                      ).toLocaleString('en-IN')}`
                    }
                  />

                  <Line
                    type="monotone"
                    dataKey="expenses"
                    strokeWidth={3}
                    dot={{ r: 5 }}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>


            <div className="chart-placeholder">

              <h3>
                Spending Categories
              </h3>

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <BarChart
                  data={categorySpendingData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="category"
                    angle={-35}
                    textAnchor="end"
                    height={80}
                  />

                  <YAxis />

                  <Tooltip
                    formatter={(value) =>
                      `₹${Number(
                        value
                      ).toLocaleString('en-IN')}`
                    }
                  />

                  <Bar
                    dataKey="amount"
                    radius={[
                      6,
                      6,
                      0,
                      0
                    ]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>


          <div className="analytics-grid">

            <div className="chart-placeholder">

              <h3>
                Income vs Expenses
              </h3>

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <BarChart
                  data={monthlySpendingData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="month"
                  />

                  <YAxis />

                  <Tooltip
                    formatter={(value) =>
                      `₹${Number(
                        value
                      ).toLocaleString('en-IN')}`
                    }
                  />

                  <Legend />

                  <Bar
                    dataKey="income"
                    name="Income"
                    radius={[
                      6,
                      6,
                      0,
                      0
                    ]}
                  />

                  <Bar
                    dataKey="expenses"
                    name="Expenses"
                    radius={[
                      6,
                      6,
                      0,
                      0
                    ]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>


          <div className="analytics-grid">

            <div className="chart-placeholder">

              <h3>
                Spending Behavior Clusters
              </h3>

              {clusters ? (

                <ResponsiveContainer
                  width="100%"
                  height={300}
                >

                  <BarChart
                    data={clusterChartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="cluster"
                    />

                    <YAxis />

                    <Tooltip
                      formatter={(
                        value,
                        name
                      ) => {

                        if (
                          name ===
                          'average'
                        ) {

                          return `₹${Number(
                            value
                          ).toLocaleString(
                            'en-IN'
                          )}`

                        }

                        return value

                      }}
                    />

                    <Legend />

                    <Bar
                      dataKey="average"
                      name="Average Transaction"
                      radius={[
                        6,
                        6,
                        0,
                        0
                      ]}
                    />

                  </BarChart>

                </ResponsiveContainer>

              ) : (

                <p>
                  Loading clustering analysis...
                </p>

              )}

            </div>

          </div>

        </section>


        {/* ===================================================
            TRANSACTIONS
        =================================================== */}

        <section
          className="insights"
          id="transactions"
        >

          <p className="eyebrow">
            TRANSACTIONS
          </p>

          <h2>
            Your transaction history.
          </h2>


          <div className="insight-card">

            {/* FILTER CONTROLS */}

            <div
              style={{
                display: 'grid',
                gridTemplateColumns:
                  'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '12px',
                marginBottom: '20px'
              }}
            >

              {/* SEARCH */}

              <input
                type="text"
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(event) =>
                  setSearchTerm(
                    event.target.value
                  )
                }
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc'
                }}
              />


              {/* CATEGORY */}

              <select
                value={categoryFilter}
                onChange={(event) =>
                  setCategoryFilter(
                    event.target.value
                  )
                }
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc'
                }}
              >

                <option value="all">
                  All Categories
                </option>

                {categories.map(
                  (category) => (

                    <option
                      key={category}
                      value={category}
                    >
                      {category}
                    </option>

                  )
                )}

              </select>


              {/* TYPE */}

              <select
                value={typeFilter}
                onChange={(event) =>
                  setTypeFilter(
                    event.target.value
                  )
                }
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc'
                }}
              >

                <option value="all">
                  All Transactions
                </option>

                <option value="income">
                  Income
                </option>

                <option value="expense">
                  Expenses
                </option>

              </select>


              {/* SORT */}

              <select
                value={sortBy}
                onChange={(event) =>
                  setSortBy(
                    event.target.value
                  )
                }
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #ccc'
                }}
              >

                <option value="date-desc">
                  Newest First
                </option>

                <option value="date-asc">
                  Oldest First
                </option>

                <option value="amount-desc">
                  Highest Amount
                </option>

                <option value="amount-asc">
                  Lowest Amount
                </option>

              </select>

            </div>


            {/* RESULT COUNT */}

            <p>
              Showing{' '}
              <strong>
                {filteredTransactions.length}
              </strong>{' '}
              of{' '}
              <strong>
                {transactions.length}
              </strong>{' '}
              transactions
            </p>


            {/* TABLE */}

            {filteredTransactions.length === 0 ? (

              <p>
                No transactions match your filters.
              </p>

            ) : (

              <div
                style={{
                  overflowX: 'auto',
                  width: '100%'
                }}
              >

                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    minWidth: '850px'
                  }}
                >

                  <thead>

                    <tr>

                      <th
                        style={{
                          textAlign: 'left',
                          padding: '12px'
                        }}
                      >
                        Date
                      </th>

                      <th
                        style={{
                          textAlign: 'left',
                          padding: '12px'
                        }}
                      >
                        Description
                      </th>

                      <th
                        style={{
                          textAlign: 'left',
                          padding: '12px'
                        }}
                      >
                        Category
                      </th>

                      <th
                        style={{
                          textAlign: 'left',
                          padding: '12px'
                        }}
                      >
                        Type
                      </th>

                      <th
                        style={{
                          textAlign: 'right',
                          padding: '12px'
                        }}
                      >
                        Amount
                      </th>

                      <th
                        style={{
                          textAlign: 'left',
                          padding: '12px'
                        }}
                      >
                        Payment Method
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {filteredTransactions.map(
                      (
                        transaction,
                        index
                      ) => (

                        <tr
                          key={`${transaction.date}-${transaction.description}-${index}`}
                        >

                          <td
                            style={{
                              padding: '12px'
                            }}
                          >
                            {
                              transaction.date
                            }
                          </td>

                          <td
                            style={{
                              padding: '12px'
                            }}
                          >
                            {
                              transaction.description
                            }
                          </td>

                          <td
                            style={{
                              padding: '12px'
                            }}
                          >
                            {
                              transaction.category
                            }
                          </td>

                          <td
                            style={{
                              padding: '12px'
                            }}
                          >
                            {
                              transaction.type
                            }
                          </td>

                          <td
                            style={{
                              padding: '12px',
                              textAlign: 'right'
                            }}
                          >
                            ₹
                            {transaction.amount.toLocaleString(
                              'en-IN'
                            )}
                          </td>

                          <td
                            style={{
                              padding: '12px'
                            }}
                          >
                            {
                              transaction.payment_method
                            }
                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

          </div>

        </section>


        {/* ===================================================
            AI INSIGHTS
        =================================================== */}

        <section
          className="insights"
          id="insights"
        >

          <p className="eyebrow">
            AI INSIGHTS
          </p>

          <h2>
            Insights from your data.
          </h2>


          <div className="insight-card">

            <h3>
              Highest spending category:{' '}
              {
                analytics
                  .highest_spending_category
                  .category
              }
            </h3>

            <p>
              Total spending in this category:{' '}
              <strong>
                ₹
                {analytics
                  .highest_spending_category
                  .amount
                  .toLocaleString(
                    'en-IN'
                  )}
              </strong>
            </p>

            <p>
              Largest expense:{' '}
              <strong>
                {
                  analytics
                    .largest_transaction
                    .description
                }
              </strong>{' '}
              — ₹
              {analytics
                .largest_transaction
                .amount
                .toLocaleString(
                  'en-IN'
                )}
            </p>

          </div>


          <div className="insight-card">

            <h3>
              Anomaly Detection
            </h3>

            <p>
              FinSight AI detected{' '}
              <strong>
                {anomalies.length}
              </strong>{' '}
              unusual transactions.
            </p>

            {anomalies.length > 0 ? (

              <div>

                {anomalies.map(
                  (
                    anomaly,
                    index
                  ) => (

                    <div
                      key={index}
                    >

                      <p>

                        <strong>
                          {
                            anomaly.description
                          }
                        </strong>

                        <br />

                        Date:{' '}
                        {
                          anomaly.date
                        }

                        <br />

                        Category:{' '}
                        {
                          anomaly.category
                        }

                        <br />

                        Amount: ₹
                        {anomaly.amount.toLocaleString(
                          'en-IN'
                        )}

                        <br />

                        Payment Method:{' '}
                        {
                          anomaly.payment_method
                        }

                      </p>

                    </div>

                  )
                )}

              </div>

            ) : (

              <p>
                No unusual transactions detected.
              </p>

            )}

          </div>


          <div className="insight-card">

            <h3>
              Expense Forecast
            </h3>

            {forecast ? (

              <>

                <p>
                  Predicted expense for next month:
                </p>

                <h3>
                  ₹
                  {forecast.predicted_expense.toLocaleString(
                    'en-IN',
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    }
                  )}
                </h3>

                <p>
                  This forecast is generated using
                  a machine learning model trained
                  on historical monthly expenses.
                </p>

              </>

            ) : (

              <p>
                Loading forecast...
              </p>

            )}

          </div>


          <div className="insight-card">

            <h3>
              Spending Behavior
            </h3>

            {clusters ? (

              <>

                <p>
                  FinSight AI grouped your expense
                  transactions into{' '}
                  <strong>
                    3 spending behavior clusters
                  </strong>{' '}
                  using K-Means clustering.
                </p>

                {clusters.summary.map(
                  (
                    cluster
                  ) => (

                    <div
                      key={
                        cluster.cluster
                      }
                    >

                      <p>

                        <strong>
                          Cluster{' '}
                          {
                            cluster.cluster
                          }
                        </strong>

                        <br />

                        Transactions:{' '}
                        {
                          cluster.count
                        }

                        <br />

                        Average transaction: ₹
                        {cluster.mean.toLocaleString(
                          'en-IN',
                          {
                            maximumFractionDigits: 2
                          }
                        )}

                        <br />

                        Range: ₹
                        {cluster.min.toLocaleString(
                          'en-IN'
                        )}{' '}
                        – ₹
                        {cluster.max.toLocaleString(
                          'en-IN'
                        )}

                      </p>

                    </div>

                  )
                )}

              </>

            ) : (

              <p>
                Loading spending behavior analysis...
              </p>

            )}

          </div>

        </section>


        {/* ===================================================
            ASK AI
        =================================================== */}

        <section
          className="insights"
          id="ask-ai"
        >

          <p className="eyebrow">
            ASK FIN SIGHT AI
          </p>

          <h2>
            Ask questions about your finances.
          </h2>

          <div className="insight-card">

            <h3>
              FinSight AI Assistant
            </h3>

            <p>
              Ask a question about your financial
              data and get an AI-generated answer
              based on your transactions.
            </p>

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              onKeyDown={
                handleQuestionKeyDown
              }
              placeholder="e.g. What is my highest spending category?"
              rows={4}
            />

            <br />

            <button
              onClick={
                askFinSight
              }
              disabled={
                aiLoading
              }
            >
              {aiLoading
                ? 'Analyzing...'
                : 'Ask FinSight AI'}
            </button>

            {aiError && (

              <p>
                <strong>
                  {aiError}
                </strong>
              </p>

            )}

            {aiAnswer && (

              <div>

                <h3>
                  AI Response
                </h3>

                <p
                  style={{
                    whiteSpace:
                      'pre-wrap'
                  }}
                >
                  {aiAnswer}
                </p>

              </div>

            )}

          </div>

        </section>

      </main>

    </div>
  )
}

export default App
