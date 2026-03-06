from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Example GET endpoint
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello, world!'})

# Example POST endpoint
@app.route('/product_forecast', methods=['POST'])
def product_forecast():
    from ML.final_code.Scenario_1 import predictions
    data = request.get_json()
    forecast_period = data['forecast_period']
    category = data.get('category',None)
    sub_category = data.get('sub_category',None)
    product_name = data.get('product_name',None)
    out_predicts = predictions(
        forecast_period = forecast_period, 
        category = category,
        sub_category = sub_category, 
        product_name = product_name
    )
    if type(out_predicts)==pd.DataFrame: 
        grouped_json = {
            month: group
                .sort_values(by='Predicted_Sales', ascending=False)
                .drop(columns='Forecast_Month')
                .to_dict(orient='records')
            for month, group in out_predicts.groupby('Forecast_Month')
        }
        out_predicts_json = jsonify(grouped_json)
    else: 
        out_predicts_json = out_predicts
    return out_predicts_json


# Example POST endpoint
@app.route('/store_forecast', methods=['POST'])
def store_forecast():
    from ML.final_code.Scenario_4 import predictions
    data = request.get_json()
    print(data)
    forecast_period = data['forecast_period']
    percentage_increase = data['percentage_increase']
    out_predicts = predictions(
        forecast_period = forecast_period, 
        percentage_increase = percentage_increase
    )
    if type(out_predicts)==pd.DataFrame: 
        grouped_json = {
            month: group
                # .sort_values(by='Predicted_Sales', ascending=False)
                .drop(columns='Forecast_Month')
                .to_dict(orient='records')
            for month, group in out_predicts.groupby('Forecast_Month')
        }
        out_predicts_json = jsonify(grouped_json)
    else: 
        out_predicts_json = out_predicts
    return out_predicts_json

# Example POST endpoint
@app.route('/customer_forecast', methods=['POST'])
def customer_forecast():
    from ML.final_code.Scenario_3 import predictions
    data = request.get_json()
    required_fields = ['Customer ID', 'Segment', 'Country', 'City', 'State', 'Region']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400  # HTTP 400 = Bad Request
    
    forecast_period = data['forecast_period']
    customer_input = {
        "Customer ID": data["Customer ID"],
        "Segment": data["Segment"],
        "Country": data["Country"],
        "City": data["City"],
        "State": data["State"],
        "Region": data["Region"]
    }
    
    out_predicts = predictions(
        forecast_period = forecast_period, 
        customer_data = customer_input
    )
    
    return out_predicts


if __name__ == '__main__':
    app.run(debug=True)
    # {'Category': 'Technology', 'Sub-Category': 'Phones', 'Product Name': 'Clarity 53712', 'Forecast_Month': '2025-12', 'Predicted_Sales': 211.24}
    # app.run(host='10.177.171.61', port=5050, debug=True)