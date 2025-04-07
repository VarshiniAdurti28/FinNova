from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_form():
    return send_from_directory('.', 'loans.html')

@app.route('/api/loan-request', methods = ['POST'])
def loan_request():
    data = request.get_json()
    loan = data.get('loanAmount')
    assets = data.get('assetValue')
    income = data.get('income')

    if loan is None or assets is None or not income:
        return jsonify(sucess=False, message = 'Invalid input'), 400
    
    if loan > assets:
        return jsonify(success=False, message='Loan denied: amount exceeds asset value.')
    
    if income == 'low' and loan > 1200000:
        return jsonify(success=False, message='Loan denied: exceeds limit for low income.')
    elif income == 'medium' and loan > 5000000:
        return jsonify(success=False, message='Loan denied: exceeds limit for medium income.')
    
    return jsonify(sucess=True, message= 'Loan approved!!')

if __name__ == '__main__':
    app.run(debug=True)