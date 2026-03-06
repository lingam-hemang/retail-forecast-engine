import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

# Define the artifacts directory globally or as a common variable
ARTIFACTS_DIR = f"{os.path.dirname(os.path.realpath(__file__))}/Scenario 3"

### 7. `load_artifacts`
def load_artifacts():
    """
    Loads the trained model, encoding objects, and unique products DataFrame from disk.

    Returns:
        tuple: A tuple containing:
            - model: The loaded trained machine learning model.
            - label_encoders (dict): Loaded LabelEncoders.
            - features (list): List of features used for training.
            - all_products_df (pd.DataFrame): Loaded DataFrame of all unique products.
    """
    print(f"Loading model artifacts from '{ARTIFACTS_DIR}'...")
    try:
        model = joblib.load(os.path.join(ARTIFACTS_DIR, 'recommendation_model.pkl'))
        label_encoders = joblib.load(os.path.join(ARTIFACTS_DIR, 'label_encoders.pkl'))
        features = joblib.load(os.path.join(ARTIFACTS_DIR, 'model_features.pkl'))
        all_products_df = joblib.load(os.path.join(ARTIFACTS_DIR, 'all_products_df.pkl')) # New line
        print("Model artifacts loaded successfully.")
        return model, label_encoders, features, all_products_df
    except FileNotFoundError:
        print(f"Error: Could not find artifacts in '{ARTIFACTS_DIR}'. Please ensure they are saved.")
        return None, None, None, None # Return None for the new artifact too
    except Exception as e:
        print(f"An error occurred while loading artifacts: {e}")
        return None, None, None, None


### 8. `predictions`
def predictions(customer_data, forecast_period): # all_products_df removed from args
    """
    Predicts the top 5 products a given customer may buy for the next few forecast months
    with their probability of purchase.
    Loads model artifacts internally, including the all_products_df.

    Args:
        customer_data (dict): Dictionary of customer attributes (e.g., {"Customer ID": "Customer B", "Segment": "Corporate"}).
        forecast_period (int): The number of months to forecast.

    Returns:
        dict: Dictionary with forecast months as keys and values as dictionaries
              mapping product names to purchase probabilities (top 5).
    """
    # --- PERFORMANCE NOTE ---
    # Loading artifacts inside this function will cause disk I/O every time it's called.
    # For high-frequency prediction services, it's more efficient to load artifacts once
    # outside this function and keep them in memory.
    # For demonstration or infrequent calls, this approach is simpler.
    print("Attempting to load model artifacts for prediction...")
    model, label_encoders, model_features, all_products_df = load_artifacts() # all_products_df added here

    if model is None or label_encoders is None or model_features is None or all_products_df is None:
        print("Failed to load necessary artifacts for prediction. Cannot proceed.")
        return {}

    print(f"Generating predictions for Customer ID: {customer_data.get('Customer ID')} for {forecast_period} months...")

    customer_id = customer_data.get("Customer ID")
    customer_segment = customer_data.get("Segment")
    customer_country = customer_data.get("Country", "Unknown")
    customer_city = customer_data.get("City", "Unknown")
    customer_state = customer_data.get("State", "Unknown")
    customer_region = customer_data.get("Region", "Unknown")

    if not customer_id:
        print("Error: 'Customer ID' not provided in customer_data.")
        return {}

    temp_df_data = {
        'Customer ID': [customer_id] * len(all_products_df),
        'Product ID': all_products_df['Product ID'],
        'Product Name': all_products_df['Product Name'],
        'Category': all_products_df['Category'],
        'Sub-Category': all_products_df['Sub-Category'],
        'Segment': [customer_segment] * len(all_products_df),
        'Country': [customer_country] * len(all_products_df),
        'City': [customer_city] * len(all_products_df),
        'State': [customer_state] * len(all_products_df),
        'Region': [customer_region] * len(all_products_df)
    }
    inference_df = pd.DataFrame(temp_df_data)

    categorical_cols_to_encode = [
        'Customer ID', 'Product ID', 'Product Name', 'Category', 'Sub-Category',
        'Segment', 'Country', 'City', 'State', 'Region'
    ]

    for col in categorical_cols_to_encode:
        encoded_col_name = f'{col}_encoded'
        if col in label_encoders and col in inference_df.columns:
            le = label_encoders[col]
            mapping_dict = {label: encoded_val for encoded_val, label in enumerate(le.classes_)}
            inference_df[encoded_col_name] = inference_df[col].astype(str).map(mapping_dict).fillna(-1).astype(int)
        else:
            inference_df[encoded_col_name] = -1
            print(f"Warning: LabelEncoder for '{col}' not found or column not in inference data. Using -1 for encoding.")

    current_time = datetime.now() # Current time is 2025-07-25 15:10:06 IST.
    inference_df['Order_Year'] = current_time.year
    inference_df['Order_Month'] = current_time.month
    inference_df['Order_Day'] = current_time.day
    inference_df['Days_to_Ship'] = 3

    X_predict_cols = [f for f in model_features if f in inference_df.columns]
    X_predict = inference_df[X_predict_cols]

    probabilities = model.predict_proba(X_predict)[:, 1]
    inference_df['probability'] = probabilities

    top_products_all = inference_df.nlargest(5, 'probability')

    forecast_results = {}
    for i in range(forecast_period):
        forecast_month_date = current_time.replace(day=1) + timedelta(days=30 * (i + 1))
        forecast_month = forecast_month_date.strftime("%Y-%m")
        month_predictions = {}
        for _, row in top_products_all.iterrows():
            month_predictions[row['Product Name']] = round(row['probability'], 2)
        forecast_results[forecast_month] = month_predictions

    print("Predictions generated.")
    return forecast_results


# --- Main Execution Block ---
if __name__ == "__main__":
    # --- 7. Make Predictions (Calling the new `predictions` function) ---
    customer_input = {
        "Customer ID": "Customer B",
        "Segment": "Corporate",
        "Country": "United States",
        "City": "Los Angeles",
        "State": "California",
        "Region": "West",
    }
    forecast_months = 2

    # Now, all_products_for_prediction_df is NOT passed to predictions
    predictions_output = predictions(
        customer_input,
        forecast_months
    )
    print("\nCustomer Recommendation Predictions:")
    print(predictions_output)
    