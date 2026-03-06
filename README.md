# Warehouse Management & Sales Forecasting

A web-based application that combines pre-trained machine learning models with an interactive UI to deliver sales forecasts and product recommendations at multiple levels: product, customer, store, and combined customer-product.

---

## Features

- **Product Forecast** — Predict monthly sales value for a specific product category and sub-category using a Random Forest Regressor.
- **Customer Forecast** — Recommend the top 5 products a customer is most likely to purchase, with purchase probabilities.
- **Store Forecast** — Predict store-wide sales by product for upcoming months, incorporating projected customer growth.
- **File Management** — Upload, browse, download, and delete CSV/XLSX/TXT/PDF data files through the browser.
- **Dark / Light Theme** — Toggle between themes; preference is persisted across pages.
- **REST API** — All forecast features are also accessible as JSON API endpoints.

---

## Project Structure

```
retail-forecast-engine/
├── app.py                        # Main Flask web application (UI routes)
├── api_app.py                    # REST API endpoints for ML predictions
├── dashboard.py                  # Dash integration module
├── scenario4_dash_app.py         # Standalone Dash app for store forecast
├── requirement.txt               # Python dependencies
├── Sample Postman Collection.json
├── static/                       # CSS and JavaScript assets
│   ├── style.css / style_light.css / style_dark.css
│   ├── dark.css / light.css
│   ├── product_forecast_form-*.css
│   ├── product_forecast_submitted-*.css
│   ├── scripts.js
│   └── theme-toggle.js
├── templates/                    # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   ├── file_management.html
│   ├── product_forecast.html / product_forecast_form.html / product_forecast_submitted.html
│   ├── customer_forecast.html
│   ├── customer_product_forecast.html
│   └── store_forecast.html
└── ML/
    ├── data/
    │   └── raw_data/
    │       └── Complete.csv       # Training dataset
    └── final code/
        ├── Scenario_1.py          # Product forecasting inference
        ├── Scenario_3.py          # Customer recommendation inference
        ├── Scenario_4.py          # Store forecasting inference
        ├── Scenario 1/            # Saved model artifacts (Scenario 1)
        │   ├── random_forest_regressor_model_sales.joblib
        │   ├── label_encoders_sales_value.joblib
        │   ├── product_avg_features_map.csv
        │   └── artifacts_info_sales_value.joblib
        ├── Scenario 3/            # Saved model artifacts (Scenario 3)
        │   ├── recommendation_model.pkl
        │   ├── label_encoders.pkl
        │   ├── model_features.pkl
        │   └── all_products_df.pkl
        ├── Scenario 4/            # Saved model artifacts (Scenario 4)
        │   ├── sales_prediction_model.joblib
        │   ├── category_encoder.joblib
        │   ├── subcategory_encoder.joblib
        │   ├── product_encoder.joblib
        │   └── prediction_context.joblib
        ├── Scenario 1.ipynb
        ├── Scenario 3.ipynb
        ├── Scenario 4.ipynb
        └── data_check.ipynb
```

---

## Tech Stack

| Layer | Libraries |
|---|---|
| Web framework | Flask 3.1, Dash 3.1, Werkzeug 3.1 |
| Machine learning | scikit-learn 1.7, TensorFlow 2.19, Keras 3.10, LightGBM 4.6, CatBoost 1.2, XGBoost 3.0 |
| Data processing | pandas 2.3, NumPy 2.1, pyarrow 20.0, joblib 1.5 |
| Visualisation | Plotly 6.2, Matplotlib 3.10, Seaborn 0.13, Bokeh 3.7 |
| Frontend | HTML / CSS / JavaScript, Flask-Humanize, Flask-Moment |

---

## Prerequisites

- Python 3.9+
- All saved model artifacts present under `ML/final code/Scenario [1|3|4]/`
- Raw dataset at `ML/data/raw_data/Complete.csv`

---

## Installation

```bash
# Clone or download the repository, then navigate into it
cd "retail-forecast-engine"

# Install all Python dependencies
pip install -r requirement.txt
```

---

## Running the Application

### Web UI (Flask)

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

### REST API server

```bash
python api_app.py
```

The API is available at `http://localhost:5000`.

### Standalone Store Forecast Dashboard (Dash)

```bash
python scenario4_dash_app.py
```

Open `http://localhost:8050`.

---

## API Reference

Import `Sample Postman Collection.json` into Postman for ready-made requests.

### `GET /api/hello`

Health check.

```json
{ "message": "Hello, world!" }
```

---

### `POST /product_forecast`

Predict monthly sales for a product.

**Request body**

```json
{
  "forecast_period": 3,
  "category": "Technology",
  "sub_category": "Phones",
  "product_name": "Apple Smart Phone, Full Size"
}
```

`product_name` is optional. When omitted, predictions are returned for all products in the sub-category.

**Response**

```json
{
  "2025-04": [
    {
      "Category": "Technology",
      "Sub-Category": "Phones",
      "Product Name": "Apple Smart Phone, Full Size",
      "Predicted_Sales": 211.24
    }
  ],
  "2025-05": [ ... ],
  "2025-06": [ ... ]
}
```

---

### `POST /store_forecast`

Predict store-wide sales with projected customer growth.

**Request body**

```json
{
  "forecast_period": 3,
  "percentage_increase": 0.34
}
```

`percentage_increase` is the expected fractional growth in customer count (e.g. `0.34` = 34 % growth).

**Response**

```json
{
  "2025-04": [
    {
      "Product_Name": "...",
      "Predicted_Sales": 5430.12,
      "Projected_Customer_Count": 512
    }
  ]
}
```

---

### `POST /customer_forecast`

Get top-5 product recommendations for a customer.

**Request body**

```json
{
  "forecast_period": 3,
  "Customer ID": "Customer 123",
  "Segment": "Corporate",
  "Country": "United States",
  "City": "Los Angeles",
  "State": "California",
  "Region": "West"
}
```

**Response**

Returns the top 5 products with predicted purchase probabilities for each forecast month.

---

## ML Models Overview

| Scenario | Purpose | Algorithm | Key inputs |
|---|---|---|---|
| Scenario 1 | Product sales forecasting | Random Forest Regressor | Category, Sub-Category, Product Name, avg price/discount/profit, cyclical month encoding |
| Scenario 3 | Customer product recommendations | Binary classification | Customer ID, Segment, Country, City, State, Region, product attributes |
| Scenario 4 | Store-level sales forecasting | Time-series regression | Year, Month, Quarter, time index, cyclical month encoding, encoded product/category/sub-category, projected customer count |

All models are pre-trained. The application performs inference only; no training occurs at runtime.

---

## File Management

Navigate to `/file-management/` in the web UI to:

- Upload files (CSV, XLSX, TXT, PDF)
- Create sub-folders
- Download or delete existing files

Uploaded files are stored under `ML/data/`.

---

## Environment Variables

The application currently uses a hardcoded Flask secret key. For production deployments, set the following environment variables before starting the server:

| Variable | Description |
|---|---|
| `FLASK_SECRET_KEY` | Secret key for session signing |
| `FLASK_ENV` | `development` or `production` |
| `FLASK_DEBUG` | `True` or `False` |

---

## Notebooks

Exploratory Jupyter notebooks are available in `ML/final code/` for each scenario:

- `Scenario 1.ipynb` — Product forecasting exploration & model training
- `Scenario 3.ipynb` — Customer recommendation exploration & model training
- `Scenario 4.ipynb` — Store forecasting exploration & model training
- `data_check.ipynb` — Raw data validation and profiling
