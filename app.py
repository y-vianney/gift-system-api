from flask import Flask, request, jsonify
from gift_system import view

app = Flask(__name__)

@app.route('/',  methods=['GET'])
def ping():
    return jsonify({'data': 'Hello World!'})

@app.route('/worker-name', methods=['POST'])
def fetch_worker_name():
    data = request.get_json(silent=True)

    if not data or 'key' not in data:
        return jsonify({'error': 'Key is required'}), 400

    key = data['key'].strip()
    if not key:
        return jsonify({'error': 'Empty key'}), 400

    wn = view(key)
    if wn is None:
        return jsonify({'error': 'Invalid key or no assignment'}), 404

    return jsonify({'data': {
        'worker_name': wn
    }}), 200

if __name__ == '__main__':
    app.run(debug=True)
