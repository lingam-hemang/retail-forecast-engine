import os
import datetime
import humanize
import psutil
from flask import (
    Flask,
    render_template,
    request,
    session,
    make_response,
    jsonify,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from dateutil.relativedelta import relativedelta 
from werkzeug.utils import secure_filename, safe_join
from flask_caching import Cache
from functools import lru_cache
from ML.Code.Predicts.scenario4 import predict_future_sales, generate_dashboard_charts_plotly

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app) 

# from dashboard import init_dash
# init_dash(app)

UPLOAD_FOLDER = "ML/data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "txt", "pdf"}

nav_items = [
    ("home", "Home"),
    ("file_management", "File Management"),
    ("product_forecast", "Product Forecast"),
    ("customer_forecast", "Customer Forecast"),
    ("customer_product_forecast", "Customer-Product Forecast"),
    ("store_forecast", "Store Forecast"),
]


def allowed_file(filename):
    return (
        "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def compute_relative_date(dt):
    if not isinstance(dt, datetime.datetime):
        return "-"
    now = datetime.datetime.now()
    delta = now - dt
    return humanize.naturaltime(delta)

def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num) < 1024.0:
            return f"{num:.2f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f} Y{suffix}"

def get_memory_usage_mb():
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss  # Resident Set Size
    mem_mb = mem_bytes / (1024 ** 2)
    return mem_mb

def get_memory_usage_mb():
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 ** 2)

@app.after_request
def log_memory_usage(response):
    if response is None:
        response = make_response("Default response")
    mem = get_memory_usage_mb()
    with open('memory_log.txt','a+') as f:
        f.write(f"Memory usage after request: {mem:.2f} MB\n")
    print(f"Memory usage after request: {mem:.2f} MB")
    return response

@app.route("/")
def home():
    return render_template(
        "home.html", nav_items=nav_items, active="home", active_page='home'
    )

@app.template_test('datetime')
def is_datetime(value):
    return isinstance(value, datetime.datetime)

@app.route('/set_date_format', methods=['POST'])
def set_date_format():
    fmt = request.form.get('date_format')
    session['date_format'] = fmt
    flash('Date format updated.', 'success')
    return redirect(request.referrer or url_for('file_management'))


# Jinja filter for relative dates
@app.template_filter()
def relative_date(dt):
    if not isinstance(dt, datetime):
        return dt
    now = datetime.now()
    return str(humanize.naturaltime(now - dt))

# Jinja filter for LLL format (e.g., Jul 19, 2025 2:30 PM)
@app.template_filter()
def lll_format(dt):
    if not isinstance(dt, datetime):
        return dt
    return dt.strftime("%b %d, %Y %I:%M %p")

@app.route("/file-management/", defaults={"subpath": ""}, methods=["GET", "POST"])
@app.route("/file-management/<path:subpath>", methods=["GET", "POST"])
def file_management(subpath):
    safe_path = safe_join(UPLOAD_FOLDER, subpath)
    if safe_path is None or not os.path.exists(safe_path):
        flash("Invalid folder path.", "warning")
        return redirect(url_for("file_management"))

    if request.method == "POST":
        # Detect which form submitted via hidden input
        action = request.form.get("action")
        
        if action == "upload":
            if "file" not in request.files:
                flash("No file part in the request.", "warning")
                return redirect(url_for("file_management", subpath=subpath))
            file = request.files["file"]
            if file.filename == "":
                flash("No file selected.", "warning")
                return redirect(url_for("file_management", subpath=subpath))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(safe_path, filename)

                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(save_path):
                    filename = f"{base}({counter}){ext}"
                    save_path = os.path.join(safe_path, filename)
                    counter += 1

                file.save(save_path)
                flash(f"File '{filename}' uploaded successfully.", "success")
                return redirect(url_for("file_management", subpath=subpath))
            else:
                flash("Invalid file type. Allowed: csv, xlsx, txt, pdf", "warning")
                return redirect(url_for("file_management", subpath=subpath))
        
        elif action == "create_folder":
            folder_name = request.form.get("folder_name", "").strip()
            if folder_name == "":
                flash("Folder name cannot be empty.", "warning")
                return redirect(url_for("file_management", subpath=subpath))
            # Sanitize folder name
            safe_folder_name = secure_filename(folder_name)
            new_folder_path = os.path.join(safe_path, safe_folder_name)
            if os.path.exists(new_folder_path):
                flash(f"Folder '{safe_folder_name}' already exists.", "warning")
                return redirect(url_for("file_management", subpath=subpath))
            try:
                os.makedirs(new_folder_path)
                flash(f"Folder '{safe_folder_name}' created successfully.", "success")
            except Exception as e:
                flash(f"Failed to create folder: {str(e)}", "warning")
            return redirect(url_for("file_management", subpath=subpath))

    entries = os.listdir(safe_path)
    entries.sort()

    items = []
    for entry in entries:
        full_entry = os.path.join(safe_path, entry)
        is_folder = os.path.isdir(full_entry)
        size = None
        if not is_folder:
            size = sizeof_fmt(os.path.getsize(full_entry))

        # Last modified time
        try:
            if not is_folder:
                mtime = os.path.getmtime(full_entry)
                last_modified = datetime.datetime.fromtimestamp(mtime) #.strftime("%Y-%m-%d %H:%M:%S")
            else: last_modified = "-"
        except Exception:
            last_modified = "N/A"

        # Determine if delete is allowed (same as before)
        relative_path = (subpath + "/" if subpath else "") + entry
        can_delete = False
        if is_folder:
            try:
                can_delete = len(os.listdir(full_entry)) == 0  # empty folder
            except Exception:
                can_delete = False
        else:
            normalized = relative_path.replace("\\", "/")
            if normalized.startswith("raw_data/") or normalized == "raw_data":
                can_delete = True

        items.append({
            "name": entry,
            "is_folder": is_folder,
            "size": size,
            "path": relative_path,
            "can_delete": can_delete,
            "last_modified": last_modified,
            "relative_modified": compute_relative_date(last_modified)
        })

    breadcrumbs = []
    if subpath:
        parts = subpath.split(os.sep)
        for i in range(len(parts)):
            crumb_path = "/".join(parts[: i + 1])
            breadcrumbs.append((parts[i], crumb_path))
    
    date_format = session.get('date_format', '%Y-%m-%d %H:%M:%S')

    return render_template(
        "file_management.html",
        active_page='file_management',
        nav_items=nav_items,
        active="file_management",
        items=items,
        breadcrumbs=breadcrumbs,
        current_path=subpath,
        date_format = date_format
    )


@app.route("/file-management/download/<path:subpath>")
def download_file(subpath):
    safe_path = safe_join(UPLOAD_FOLDER, subpath)
    if safe_path is None or not os.path.isfile(safe_path):
        flash(f"File '{subpath}' not found.", "warning")
        return redirect(url_for("file_management"))

    directory = os.path.dirname(safe_path)
    filename = os.path.basename(safe_path)
    return send_from_directory(directory, filename, as_attachment=True)


@app.route("/file-management/delete/<path:subpath>", methods=["POST"])
def delete_file(subpath):
    safe_path = safe_join(UPLOAD_FOLDER, subpath)
    if safe_path is None or not os.path.exists(safe_path):
        flash(f"File or folder '{subpath}' not found.", "warning")
        return redirect(url_for("file_management"))

    try:
        if os.path.isdir(safe_path):
            if os.listdir(safe_path):
                flash(f"Folder '{subpath}' is not empty, cannot delete.", "warning")
            else:
                os.rmdir(safe_path)
                flash(f"Folder '{subpath}' deleted successfully.", "success")
        else:
            os.remove(safe_path)
            flash(f"File '{subpath}' deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting '{subpath}': {str(e)}", "warning")

    parent_path = os.path.dirname(subpath)
    return redirect(url_for("file_management", subpath=parent_path))


@app.route("/product-forecast", methods=["GET", "POST"])
# def product_forecast():
#     return render_template("product_forecast_form.html", nav_items=nav_items, active_page="product_forecast", active="product_forecast", title="Product Forecast")
def product_forecast():
    if request.method == "POST":
        if "submit" in request.form:
            try:
                forecast_period = int(request.form.get("forecast_period", 0))
                if forecast_period < 1:
                    flash("Forecast period must be at least 1.", "error")
                    return redirect(url_for("product_forecast"))

                # Get optional fields (empty string if not provided)
                category = request.form.get("category", "").strip() or None
                sub_category = request.form.get("sub_category", "").strip() or None
                product_name = request.form.get("product_name", "").strip() or None

                # Store in session
                session['forecast_period'] = forecast_period
                session['category'] = category
                session['sub_category'] = sub_category
                session['product_name'] = product_name

                return render_template(
                    "product_forecast_submitted.html",
                    nav_items=nav_items,
                    active_page="product_forecast",
                    active="product_forecast",
                    title="Product Forecast Submitted",
                    forecast_period=forecast_period,
                    category=category,
                    sub_category=sub_category,
                    product_name=product_name
                )
            except ValueError:
                flash("Invalid forecast period. Please enter a valid integer.", "error")
                return redirect(url_for("product_forecast"))

        elif "reset" in request.form:
            session.pop('forecast_period', None)
            session.pop('category', None)
            session.pop('sub_category', None)
            session.pop('product_name', None)
            return redirect(url_for("product_forecast"))

    # GET request: check if forecast_period in session
    forecast_period = session.get('forecast_period')
    if forecast_period:
        return render_template(
            "product_forecast_submitted.html",
            nav_items=nav_items,
            active_page="product_forecast",
            active="product_forecast",
            title="Product Forecast Submitted",
            forecast_period=forecast_period,
            category=session.get('category'),
            sub_category=session.get('sub_category'),
            product_name=session.get('product_name')
        )

    # Show initial form if no session data
    return render_template(
        "product_forecast_form.html",
        nav_items=nav_items,
        active_page="product_forecast",
        active="product_forecast",
        title="Product Forecast"
    )

@app.route("/customer-forecast")
def customer_forecast():
    return render_template("customer_forecast.html", nav_items=nav_items, active_page="customer_forecast", active="customer_forecast", title="Customer Forecast")

@app.route("/customer-product-forecast")
def customer_product_forecast():
    return render_template("customer_product_forecast.html", nav_items=nav_items, active_page="customer_product_forecast", active="customer_product_forecast", title="Customer-Product Forecast")

@app.route("/store-forecast")
def store_forecast():
    return render_template("customer_product_forecast.html", nav_items=nav_items, active_page="store_forecast", active="store_forecast", title="Store Forecast")


# # AJAX endpoint to fetch subcategories
# @app.route('/_get_subcategories', methods=['POST'])
# def get_subcategories(df):
#     selected_category = request.form.get('category')
    
#     filtered_df = df.copy()
#     if selected_category != 'All':
#         filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
#     subcategories = ['All'] + sorted(filtered_df['Sub-Category'].unique().tolist())
#     return jsonify(subcategories=subcategories)

# # AJAX endpoint to fetch products
# @app.route('/_get_products', methods=['POST'])
# def get_products(df):
#     selected_category = request.form.get('category')
#     selected_subcategory = request.form.get('subcategory')

#     filtered_df = df.copy()
#     if selected_category != 'All':
#         filtered_df = filtered_df[filtered_df['Category'] == selected_category]
#     if selected_subcategory != 'All':
#         filtered_df = filtered_df[filtered_df['Sub-Category'] == selected_subcategory]

#     products = sorted(filtered_df['Product Name'].unique().tolist())
#     if not products:
#         products = ['No Products']
    
#     return jsonify(products=['All'] + products)

# # New AJAX endpoint to get parent category for a subcategory
# @app.route('/_get_parent_category', methods=['POST'])
# def get_parent_category(df):
#     selected_subcategory = request.form.get('subcategory')
    
#     parent_category = 'All' # Default
#     if selected_subcategory != 'All' and selected_subcategory in df['Sub-Category'].values:
#         parent_category = df[df['Sub-Category'] == selected_subcategory]['Category'].iloc[0]
    
#     return jsonify(parent_category=parent_category)

# # New AJAX endpoint to get parent category and subcategory for a product
# @app.route('/_get_parent_details_for_product', methods=['POST'])
# def get_parent_details_for_product(df):
#     selected_product = request.form.get('product')
    
#     parent_category = 'All'
#     parent_subcategory = 'All'

#     if selected_product != 'All' and selected_product != 'No Products' and selected_product in df['Product Name'].values:
#         product_row = df[df['Product Name'] == selected_product].iloc[0]
#         parent_category = product_row['Category']
#         parent_subcategory = product_row['Sub-Category']
    
#     return jsonify(category=parent_category, subcategory=parent_subcategory)


# @app.route("/store-forecast", methods=['GET', 'POST'])
# @lru_cache
# def store_forecast():
    
#     file_path = f'{os.getcwd()}/ML/data/raw_data/Scenario4.csv'
#     pred_df = predict_future_sales(f'{os.getcwd()}/ML/models/',file_path,5,5)
    
#     all_categories = sorted(pred_df['Category'].unique())
#     all_subcategories = sorted(pred_df['Sub-Category'].unique())
#     all_products = sorted(pred_df['Product Name'].unique())

#     # Initialize filter values from request args or defaults
#     selected_category = request.args.get('category', 'All')
#     selected_subcategory = request.args.get('subcat', 'All')
#     selected_product = request.args.get('product', 'All')
#     selected_top_n = int(request.args.get('top_n', 10))
#     # Apply filters to determine available options for subsequent dropdowns
#     filtered_df = pred_df.copy()

#     # if selected_category != 'All':
#     #     filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
#     # # Update available subcategories based on category selection
#     # available_subcategories = ['All'] + sorted(filtered_df['Sub-Category'].unique().tolist())

#     # if selected_subcategory != 'All':
#     #     filtered_df = filtered_df[filtered_df['Sub-Category'] == selected_subcategory]

#     # # Update available products based on category and subcategory selection
#     # available_products = ['All'] + sorted(filtered_df['Product Name'].unique().tolist())
#     # if not available_products: # If no products found for combination
#     #     available_products = ['No Products']


#     # # Generate charts for the initial load or full form submission
#     # chart_data = generate_dashboard_charts_plotly(
#     #     pred_df=pred_df, # Always pass the full DataFrame to the chart function
#     #     selected_category=selected_category,
#     #     selected_subcategory=selected_subcategory,
#     #     selected_product=selected_product,
#     #     selected_top_n=selected_top_n
#     # )

#     # return render_template(
#     #     'store_forecast.html',
#     #     trend_chart_html=chart_data['trend_chart_html'],
#     #     top_products_chart_html=chart_data['top_products_chart_html'],
#     #     categories=['All'] + all_categories, # Pass all categories for the first dropdown
#     #     available_subcategories=available_subcategories, # Pass filtered subcategories
#     #     available_products=available_products, # Pass filtered products
#     #     selected_category=selected_category,
#     #     selected_subcategory=selected_subcategory,
#     #     selected_product=selected_product,
#     #     selected_top_n=selected_top_n
#     # )

#     # Dynamic updates for subcategory and product options based on selected category
#     available_subcategories = ['All'] + sorted(
#         pred_df[pred_df['Category'] == selected_category]['Sub-Category'].unique()
#     ) if selected_category != 'All' else ['All'] + all_subcategories

#     temp_df_for_products = pred_df
#     if selected_category != 'All':
#         temp_df_for_products = temp_df_for_products[temp_df_for_products['Category'] == selected_category]
#     if selected_subcategory != 'All':
#         temp_df_for_products = temp_df_for_products[temp_df_for_products['Sub-Category'] == selected_subcategory]

#     available_products = ['All'] + sorted(temp_df_for_products['Product Name'].unique())
#     if not available_products:
#         available_products = ['No Products']
#     chart_outputs = generate_dashboard_charts_plotly(
#         pred_df,
#         selected_category,
#         selected_subcategory,
#         selected_product,
#         selected_top_n
#     )
#     return render_template(
#         'store_forecast.html',
#         categories=['All'] + all_categories,
#         available_subcategories=available_subcategories,
#         available_products=available_products,
#         selected_category=selected_category,
#         selected_subcategory=selected_subcategory,
#         selected_product=selected_product,
#         selected_top_n=selected_top_n,
#         trend_chart_html=chart_outputs['trend_chart_html'], # Access from dictionary
#         top_products_chart_html=chart_outputs['top_products_chart_html'] # Access from dictionary
#     )
#     # return render_template("store_forecast.html", nav_items=nav_items, active_page="store_forecast", active="store_forecast", title="Store Forecast")


if __name__ == "__main__":
    with open('memory_log.txt','w') as f:
        f.write('')
    app.run(debug=True)
