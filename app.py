from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
from io import BytesIO
import openpyxl
import warnings
from flask_cors import CORS  # Import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)  # You can pass additional parameters to configure CORS more specifically

# Folder for uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Suppress warnings from openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Load bank codes from Excel file
def load_bank_codes():
    # Load bank code Excel file (adjust the file path)
    bank_codes_file = 'path_to_bank_codes.xlsx'
    return pd.read_excel(bank_codes_file)

# Function to find error analysis
def find_error_and_analysis(key, code, message):
    bank_code = load_bank_codes()  # Load bank code data from Excel
    result = bank_code[(bank_code['key'] == key) & (bank_code['code'] == code)]
    
    if not result.empty:
        analysis = result['analysis'].values[0]  # Get the first matching analysis
        error_type = result['error type'].values[0]  # Get the first matching error type
        return analysis, error_type, False
    else:
        print('Analysis not found')
        new_analysis = input(f"Input analysis for '{code}' - '{message}' : ")
        new_error_type = "Technical Error"
        new_error_typ_answer = input(f"Is technical error?(Y/N/Other): ")
        if new_error_typ_answer.lower() == "N":
            new_error_type = "Business Error"
        elif new_error_typ_answer.lower() == "Y":
            new_error_type = "Technical Error"
        else:
            new_error_type = input(f"Input new error type : ")
        return new_analysis, new_error_type, True

# Route for the main page
@app.route('/')
def index():
    return "Flask API for merge CSV and CSV to Excel"

# API to merge CSV files
@app.route('/merge-csv', methods=['POST'])
def merge_csv():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({"error": "No files provided"}), 400

    all_dataframes = []
    headers = None

    for file in files:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file, delimiter='|')

            # Align headers
            if headers is None:
                headers = df.columns
            df = df.reindex(columns=headers, fill_value='')

            all_dataframes.append(df)

    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        merged_csv = merged_df.to_csv(index=False)

        return send_file(BytesIO(merged_csv.encode()), 
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name='merged_data.csv')
    else:
        return jsonify({"error": "No valid CSV files found"}), 400

# API for CSV to Excel conversion
@app.route('/csv-to-excel', methods=['POST'])
def csv_to_excel():
    file = request.files.get('file')
    if file is None or not file.filename.endswith('.csv'):
        return jsonify({"error": "No CSV file provided"}), 400

    try:
        csv_data = pd.read_csv(file, delimiter='|')
        excel_file = BytesIO()

        # Save CSV as Excel
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            csv_data.to_excel(writer, index=False, sheet_name='Sheet1')

        excel_file.seek(0)
        return send_file(excel_file, 
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True,
                         download_name=file.filename.replace('.csv', '.xlsx'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
