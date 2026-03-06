import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import joblib
import os

# --- Global Constants ---
ARTIFACTS_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/Scenario 1' # Reverted to old name
MODEL_FILENAME = 'random_forest_regressor_model_sales.joblib' # Reverted to .joblib for RF
LABEL_ENCODERS_FILENAME = 'label_encoders_sales_value.joblib'
PRODUCT_AVG_FEATURES_MAP_FILENAME = 'product_avg_features_map.csv'
ARTIFACTS_INFO_FILENAME = 'artifacts_info_sales_value.joblib'

FEATURE_COLUMNS = ['Category', 'Sub-Category', 'Product Name',
                   'Average_Price_Per_Unit', 'Average_Discount', 'Average_Profit_Per_Sale',
                   'Month_sin', 'Month_cos'] # Reverted: Removed 'Customer_Increase_Percentage'
TARGET_COLUMN = 'MonthlySales'

# Categorical columns that need Label Encoding (remains the same)
CATEGORICAL_FEATURES = ['Category', 'Sub-Category', 'Product Name']


# --- 7. load_artifacts (REVERTED - Random Forest Model, no Scaler) ---
def load_artifacts(artifacts_dir: str = ARTIFACTS_DIR) -> tuple:
    """
    Loads the trained model, label encoders, feature columns, target column,
    and the product average features map from the specified directory.
    
    Args:
        artifacts_dir (str): Path to the directory where artifacts are saved.
        
    Returns:
        tuple: (loaded_model, loaded_label_encoders, loaded_feature_columns,
                loaded_target_column, loaded_product_avg_features_map)
    """
    print(f"Loading artifacts from '{artifacts_dir}'...")
    try:
        loaded_model = joblib.load(os.path.join(artifacts_dir, MODEL_FILENAME)) # Reverted model load
        loaded_label_encoders = joblib.load(os.path.join(artifacts_dir, LABEL_ENCODERS_FILENAME))
        artifacts_info = joblib.load(os.path.join(artifacts_dir, ARTIFACTS_INFO_FILENAME))
        loaded_feature_columns = artifacts_info['feature_columns']
        loaded_target_column = artifacts_info['target_column']
        
        loaded_product_avg_features_map = pd.read_csv(os.path.join(artifacts_dir, PRODUCT_AVG_FEATURES_MAP_FILENAME))
        
        print("Artifacts loaded successfully.")
        return loaded_model, loaded_label_encoders, loaded_feature_columns, \
               loaded_target_column, loaded_product_avg_features_map
    except FileNotFoundError as e:
        raise FileNotFoundError(f"One or more artifact files not found in {artifacts_dir}. Error: {e}")
    except Exception as e:
        raise Exception(f"An error occurred while loading artifacts: {e}")

# --- 8. predictions (REVERTED to previous flexible DataFrame/Dict output) ---
def predictions(
    forecast_period: int, 
    category: str = None, 
    sub_category: str = None, 
    product_name: str = None
) -> [pd.DataFrame, dict]: 
    """
    Predicts the total sales value for specific product combinations for the next few months,
    allowing for flexible input on product features (Category, Sub-Category, Product Name).
    
    Artifacts are loaded internally within this function. Uses dateutil.relativedelta for month-wise forecasting.

    Args:
        forecast_period (int): Number of months to forecast.
        category (str, optional): Specific Category to filter predictions. Defaults to None.
        sub_category (str, optional): Specific Sub-Category to filter predictions. Defaults to None.
        product_name (str, optional): Specific Product Name to filter predictions. Defaults to None.

    Returns:
        pd.DataFrame: If multiple product combinations are predicted.
        dict: If a single, specific product (Category, Sub-Category, AND Product Name all specified)
              is requested.
    """
    print("Loading artifacts for prediction...")
    # Load artifacts internally
    loaded_model, loaded_label_encoders, loaded_feature_columns, \
        loaded_target_column, loaded_product_avg_features_map = load_artifacts()
    print("Artifacts loaded. Generating predictions...")

    current_time_for_forecast = datetime.now()
    all_raw_predictions = [] 

    target_products_df = loaded_product_avg_features_map.copy()

    if category:
        target_products_df = target_products_df[target_products_df['Category'] == category]
    if sub_category:
        target_products_df = target_products_df[target_products_df['Sub-Category'] == sub_category]
    if product_name:
        target_products_df = target_products_df[target_products_df['Product Name'] == product_name]

    if target_products_df.empty:
        print("No product combinations found matching the provided criteria. Returning empty output.")
        if category and sub_category and product_name:
            return {}
        else:
            return pd.DataFrame(columns=['Category', 'Sub-Category', 'Product Name', 'Forecast_Month', 'Predicted_Sales'])

    return_single_product_dict = (category is not None and sub_category is not None and product_name is not None and len(target_products_df) == 1)
    
    single_product_forecasts = {}

    for idx, product_row in target_products_df.iterrows():
        current_product_category = product_row['Category']
        current_product_sub_category = product_row['Sub-Category']
        current_product_name = product_row['Product Name']

        avg_price = product_row['Average_Price_Per_Unit']
        avg_discount = product_row['Average_Discount']
        avg_profit = product_row['Average_Profit_Per_Sale']

        for i in range(forecast_period):
            # MODIFIED LINE: Use relativedelta for month-wise forecasting
            forecast_date = current_time_for_forecast + relativedelta(months=(i + 1))
            
            forecast_month_str = forecast_date.strftime('%Y-%m')
            forecast_month_num = forecast_date.month 

            month_sin = np.sin(2 * np.pi * forecast_month_num / 12)
            month_cos = np.cos(2 * np.pi * forecast_month_num / 12)

            current_input_data = {
                'Category': current_product_category,
                'Sub-Category': current_product_sub_category,
                'Product Name': current_product_name,
                'Average_Price_Per_Unit': avg_price,
                'Average_Discount': avg_discount,
                'Average_Profit_Per_Sale': avg_profit,
                'Month_sin': month_sin,
                'Month_cos': month_cos
            }
            input_df_for_prediction = pd.DataFrame([current_input_data])
            
            input_df_for_prediction = input_df_for_prediction.reindex(columns=loaded_feature_columns, fill_value=np.nan)

            for col in CATEGORICAL_FEATURES:
                if col in loaded_label_encoders:
                    le = loaded_label_encoders[col]
                    val_to_transform = str(input_df_for_prediction[col].iloc[0]) 
                    
                    if val_to_transform in le.classes_:
                        input_df_for_prediction[col] = le.transform([val_to_transform])[0]
                    else:
                        unknown_id = len(le.classes_) 
                        input_df_for_prediction[col] = unknown_id
                        print(f"Warning: Value '{val_to_transform}' in column '{col}' not seen during training. Assigned unknown ID: {unknown_id}.")
            
            predicted_sales_value = loaded_model.predict(input_df_for_prediction)[0]
            
            if return_single_product_dict:
                single_product_forecasts[forecast_month_str] = round(predicted_sales_value, 2)
            else:
                all_raw_predictions.append({
                    'Category': current_product_category,
                    'Sub-Category': current_product_sub_category,
                    'Product Name': current_product_name,
                    'Forecast_Month': forecast_month_str,
                    'Predicted_Sales': round(predicted_sales_value, 2)
                })
        
    print("Total sales value predictions complete.")

    if return_single_product_dict:
        return single_product_forecasts
    else:
        return pd.DataFrame(all_raw_predictions)
    
if __name__ == '__main__':
    print("\nScenario 2: Predicting for 'Electronics' category for next 2 months (Expected: DataFrame)")
    predictions_category = predictions(
        forecast_period=5,
        category='Technology' # Changed to Technology for common synthetic data
    )
    print(f"Shape: {predictions_category.shape}, Type: {type(predictions_category)}")
    print(predictions_category)
        