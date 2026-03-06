import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import warnings
import os

# Suppress all warnings
warnings.filterwarnings("ignore")

# Define the directory for artifacts
ARTIFACTS_DIR = f"{os.path.dirname(os.path.realpath(__file__))}/Scenario 4"


def load_artifacts(filepath_model='sales_prediction_model.joblib',
                   filepath_product_encoder='product_encoder.joblib',
                   filepath_category_encoder='category_encoder.joblib',
                   filepath_subcategory_encoder='subcategory_encoder.joblib',
                   filepath_prediction_context='prediction_context.joblib'):
    """
    Loads a previously trained model, encoders, and prediction context from disk.
    """
    model_path = os.path.join(ARTIFACTS_DIR, filepath_model)
    product_encoder_path = os.path.join(ARTIFACTS_DIR, filepath_product_encoder)
    category_encoder_path = os.path.join(ARTIFACTS_DIR, filepath_category_encoder)
    subcategory_encoder_path = os.path.join(ARTIFACTS_DIR, filepath_subcategory_encoder)
    prediction_context_path = os.path.join(ARTIFACTS_DIR, filepath_prediction_context)

    if not all(os.path.exists(p) for p in [model_path, product_encoder_path, category_encoder_path, subcategory_encoder_path, prediction_context_path]):
        raise FileNotFoundError(f"One or more artifacts not found in {ARTIFACTS_DIR}. Please ensure the model has been trained and saved.")

    model = joblib.load(model_path)
    product_encoder = joblib.load(product_encoder_path) 
    category_encoder = joblib.load(category_encoder_path) 
    subcategory_encoder = joblib.load(subcategory_encoder_path) 
    
    prediction_context = joblib.load(prediction_context_path)
    last_historical_time_index = prediction_context['last_historical_time_index']
    last_month_customer_count = prediction_context['last_month_customer_count'] 
    product_info_map = prediction_context['product_info_map']
    
    print(f"\nModel loaded from {model_path}")
    print(f"Encoders loaded.")
    print(f"Prediction context loaded from {prediction_context_path}")
    
    return model, product_encoder, category_encoder, subcategory_encoder, last_historical_time_index, last_month_customer_count, product_info_map

def make_predictions(prediction_input: dict, output_format='dataframe'):
    """
    Generates sales predictions for each product for the next month(s) based on
    time and product-specific features. Customer count projections are now calculated
    and included in the output, but not as a model input.
    This function now loads artifacts internally.

    Args:
        prediction_input (dict): Dictionary containing "percentage_increase" and "Forecast Period".
        output_format (str): Desired output format. Can be 'dataframe' or 'json'.

    Returns:
        pd.DataFrame or dict: Sales predictions in the specified format.
    """
    # Load artifacts internally
    model, product_encoder, category_encoder, subcategory_encoder, \
    last_historical_time_index, last_month_customer_count, product_info_map = load_artifacts()

    percentage_increase = prediction_input["percentage_increase"]
    forecast_period = prediction_input["Forecast Period"]

    forecast_results = {} 
    all_predictions_list = [] 

    today_for_forecast_start = datetime.now()
    
    current_projected_customer_count = last_month_customer_count 

    print(f"\nStarting forecast from {today_for_forecast_start.strftime('%Y-%m-%d')} based on last historical customer count of {last_month_customer_count:.2f}")

    for i in range(forecast_period):
        target_date = today_for_forecast_start + relativedelta(months=i)
        
        forecast_month_str = target_date.strftime('%Y-%m')

        if isinstance(percentage_increase, (int, float)):
            current_pct_increase = percentage_increase
        elif isinstance(percentage_increase, list):
            if i < len(percentage_increase):
                current_pct_increase = percentage_increase[i]
            else:
                current_pct_increase = percentage_increase[-1]
        else:
            raise ValueError("Invalid format for 'percentage_increase'. Must be a single number or a list.")

        current_projected_customer_count *= (1 + current_pct_increase / 100) 

        forecast_time_index = last_historical_time_index + (i + 1)
        
        forecast_quarter = (target_date.month - 1) // 3 + 1

        forecast_month_sin = np.sin(2 * np.pi * target_date.month / 12)
        forecast_month_cos = np.cos(2 * np.pi * target_date.month / 12)

        month_predictions = {}
        for product_name, p_info in product_info_map.items():
            prediction_df = pd.DataFrame([{
                'Year': target_date.year,
                'Month': target_date.month,
                'Quarter': forecast_quarter,
                'Time_Index': forecast_time_index,
                'Month_sin': forecast_month_sin,
                'Month_cos': forecast_month_cos,
                'Product_Name_Encoded': p_info['Product_Name_Encoded'],
                'Category_Encoded': p_info['Category_Encoded'],
                'SubCategory_Encoded': p_info['SubCategory_Encoded']
                # Customer_Count_Monthly is NOT included here as a feature for the model
            }])
            
            predicted_sales = model.predict(prediction_df)[0]
            rounded_predicted_sales = max(0, round(predicted_sales))
            
            month_predictions[product_name] = rounded_predicted_sales

            all_predictions_list.append({
                'Forecast_Month': forecast_month_str,
                'Product_Name': product_name,
                'Predicted_Sales': rounded_predicted_sales,
                'Projected_Customer_Count': round(current_projected_customer_count, 2) 
            })

        forecast_results[forecast_month_str] = month_predictions

    print("\nSales predictions generated:")
    
    if output_format == 'dataframe':
        df_predictions = pd.DataFrame(all_predictions_list)
        # print(df_predictions.to_string())
        return df_predictions
    elif output_format == 'json':
        # print(forecast_results)
        return forecast_results
    else:
        raise ValueError("Invalid output_format. Choose 'dataframe' or 'json'.")


if __name__ == "__main__":
    print("\n--- Initiating Sales Predictions from Today ---")

    prediction_input_1 = {
        "percentage_increase": 5, 
        "Forecast Period": 3 
    }
    print("\nPrediction with constant 5% monthly customer increase (DataFrame output):")
    forecast_df = make_predictions(prediction_input_1, output_format='dataframe')
    print("\nType of output for forecast_df:", type(forecast_df))
    