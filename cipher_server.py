#!/usr/bin/env python3
"""
HTTP Server wrapper untuk cipher_mini.c
Jalankan dengan: python cipher_server.py
Akses di: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
import subprocess
import json
import os
import base64

app = Flask(__name__)

# Path ke executable cipher
CIPHER_EXE = "./cipher_mini.exe"
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cipher - Enkripsi/Dekripsi</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        input[type="text"],
        input[type="number"],
        select,
        textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
            font-family: 'Courier New', monospace;
        }
        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 25px;
        }
        button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .encrypt-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .encrypt-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .decrypt-btn {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .decrypt-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4);
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
            border-left: 4px solid #667eea;
            display: none;
        }
        .result.show {
            display: block;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .result-title {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
            font-size: 12px;
            text-transform: uppercase;
        }
        .result-content {
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #333;
            background: white;
            padding: 10px;
            border-radius: 3px;
            max-height: 200px;
            overflow-y: auto;
        }
        .error {
            border-left-color: #f5576c;
        }
        .error .result-title {
            color: #f5576c;
        }
        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            font-size: 12px;
            margin: 10px 0;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 5px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .info {
            background: #f0f4ff;
            border: 1px solid #d0deff;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            color: #667eea;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 CIPHER</h1>
        <p class="subtitle">Enkripsi & Dekripsi Teks</p>
        
        <div class="info">
            <strong>ℹ️ Cara Kerja:</strong> Program menggunakan algoritma CBC dengan substitusi, rotasi bit, dan diffusion
        </div>

        <form id="cipherForm">
            <div class="form-group">
                <label for="cipherName">Nama Cipher:</label>
                <input type="text" id="cipherName" value="MySecretCipher" required>
            </div>

            <div class="form-group">
                <label for="key">Kunci (Key):</label>
                <input type="text" id="key" value="mykey123" required>
            </div>

            <div class="form-group">
                <label for="mode">Mode:</label>
                <select id="mode">
                    <option value="CBC">CBC</option>
                    <option value="CFB">CFB</option>
                </select>
            </div>

            <div class="form-group">
                <label for="rounds">Ronde (4-16):</label>
                <input type="number" id="rounds" min="4" max="16" value="8">
            </div>

            <div class="form-group">
                <label for="text">Teks Plaintext:</label>
                <textarea id="text" placeholder="Masukkan teks yang ingin dienkripsi..." required></textarea>
            </div>

            <div class="button-group">
                <button type="button" class="encrypt-btn" onclick="encrypt()">🔒 Enkripsi</button>
                <button type="button" class="decrypt-btn" onclick="toggleDecrypt()">🔓 Dekripsi</button>
            </div>

            <div id="decryptInput" style="display: none; margin-top: 15px;">
                <div class="form-group">
                    <label for="ciphertext">Ciphertext (untuk Dekripsi):</label>
                    <textarea id="ciphertext" placeholder="Masukkan ciphertext yang ingin didekripsi..."></textarea>
                </div>
                <button type="button" class="decrypt-btn" onclick="decrypt()" style="width: 100%;">🔓 Dekripsi Sekarang</button>
            </div>
        </form>

        <div class="loading" id="loading">
            <span class="spinner"></span> Memproses...
        </div>

        <div class="result" id="result">
            <div class="result-title" id="resultTitle">Hasil</div>
            <div class="result-content" id="resultContent"></div>
        </div>
    </div>

    <script>
        function showLoading(show = true) {
            const loading = document.getElementById('loading');
            if (show) {
                loading.classList.add('show');
            } else {
                loading.classList.remove('show');
            }
        }

        function showResult(title, content, isError = false) {
            const result = document.getElementById('result');
            const resultTitle = document.getElementById('resultTitle');
            const resultContent = document.getElementById('resultContent');
            
            resultTitle.textContent = title;
            resultContent.textContent = content;
            
            result.classList.remove('error', 'show');
            if (isError) {
                result.classList.add('error');
            }
            result.classList.add('show');
            showLoading(false);
        }

        function toggleDecrypt() {
            const decryptInput = document.getElementById('decryptInput');
            decryptInput.style.display = decryptInput.style.display === 'none' ? 'block' : 'none';
        }

        async function encrypt() {
            const cipherName = document.getElementById('cipherName').value;
            const key = document.getElementById('key').value;
            const mode = document.getElementById('mode').value;
            const rounds = parseInt(document.getElementById('rounds').value);
            const text = document.getElementById('text').value;

            if (!text) {
                showResult('Error', 'Teks tidak boleh kosong!', true);
                return;
            }

            showLoading(true);

            try {
                const response = await fetch('/api/encrypt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cipher_name: cipherName,
                        key: key,
                        mode: mode,
                        rounds: rounds,
                        text: text
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    document.getElementById('ciphertext').value = data.ciphertext;
                    showResult('✅ Enkripsi Berhasil', data.ciphertext);
                } else {
                    showResult('❌ Error', data.error || 'Enkripsi gagal', true);
                }
            } catch (err) {
                showResult('❌ Error', err.message, true);
            }
        }

        async function decrypt() {
            const cipherName = document.getElementById('cipherName').value;
            const key = document.getElementById('key').value;
            const mode = document.getElementById('mode').value;
            const rounds = parseInt(document.getElementById('rounds').value);
            const ciphertext = document.getElementById('ciphertext').value;

            if (!ciphertext) {
                showResult('Error', 'Ciphertext tidak boleh kosong!', true);
                return;
            }

            showLoading(true);

            try {
                const response = await fetch('/api/decrypt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cipher_name: cipherName,
                        key: key,
                        mode: mode,
                        rounds: rounds,
                        ciphertext: ciphertext
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showResult('✅ Dekripsi Berhasil', data.plaintext);
                } else {
                    showResult('❌ Error', data.error || 'Dekripsi gagal', true);
                }
            } catch (err) {
                showResult('❌ Error', err.message, true);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/encrypt', methods=['POST'])
def encrypt():
    try:
        data = request.get_json()
        cipher_name = data.get('cipher_name', 'Cipher')
        key = data.get('key', '')
        mode = data.get('mode', 'CBC')
        rounds = int(data.get('rounds', 8))
        text = data.get('text', '')

        if not key or not text:
            return jsonify({'error': 'Key dan text harus diisi'}), 400

        # Validasi rounds
        if rounds < 4 or rounds > 16:
            return jsonify({'error': 'Rounds harus antara 4-16'}), 400

        # Buat input untuk program C (1 = enkripsi)
        input_data = f"{cipher_name}\n{key}\n{mode}\n{rounds}\n1\n{text}\n"

        # Jalankan program cipher
        result = subprocess.run(
            [CIPHER_EXE],
            cwd=WORK_DIR,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            return jsonify({'error': f'Enkripsi gagal'}), 500

        # Parse output - cari baris yang berisi format name.mode.base64
        import re
        output = result.stdout + result.stderr
        
        # Cari pattern: CIPHERTEXT atau baris dengan format [name].[mode].[base64]
        ciphertext = None
        for line in output.split('\n'):
            line = line.strip()
            # Cari pattern: word.word.base64sequence
            match = re.search(r'([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9+/=]+)', line)
            if match:
                ciphertext = match.group(1)
                break

        if not ciphertext:
            return jsonify({'error': 'Tidak dapat mengekstrak ciphertext'}), 500

        return jsonify({'ciphertext': ciphertext})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Program timeout'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/decrypt', methods=['POST'])
def decrypt():
    try:
        data = request.get_json()
        cipher_name = data.get('cipher_name', 'Cipher')
        key = data.get('key', '')
        mode = data.get('mode', 'CBC')
        rounds = int(data.get('rounds', 8))
        ciphertext = data.get('ciphertext', '')

        if not key or not ciphertext:
            return jsonify({'error': 'Key dan ciphertext harus diisi'}), 400

        # Validasi rounds
        if rounds < 4 or rounds > 16:
            return jsonify({'error': 'Rounds harus antara 4-16'}), 400

        # Buat input untuk program C (2 = dekripsi)
        input_data = f"{cipher_name}\n{key}\n{mode}\n{rounds}\n2\n{ciphertext}\n"

        # Jalankan program cipher
        result = subprocess.run(
            [CIPHER_EXE],
            cwd=WORK_DIR,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            return jsonify({'error': f'Dekripsi gagal'}), 500

        # Parse output - cari plaintext
        import re
        output = result.stdout + result.stderr
        plaintext = None

        for line in output.split('\n'):
            line_clean = line.strip()
            # Skip lines yang berisi decorator atau info lain
            if line_clean and not line_clean.startswith('┌') and not line_clean.startswith('│') and not line_clean.startswith('└') and not line_clean.startswith('PLAINTEXT') and len(line_clean) > 2:
                # Cari baris yang tampaknya plaintext (tidak ada format cipher)
                if '.' not in line_clean or ('.' in line_clean and not re.search(r'[A-Za-z0-9+/=]{20,}', line_clean)):
                    plaintext = line_clean
                    break

        if not plaintext:
            return jsonify({'error': 'Tidak dapat mengekstrak plaintext'}), 500

        return jsonify({'plaintext': plaintext})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Program timeout'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🔐 CIPHER SERVER - Running on http://localhost:5000")
    print("="*60)
    print("  Buka browser dan akses: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='localhost', port=5000)
