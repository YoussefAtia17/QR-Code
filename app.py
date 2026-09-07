import os
from flask import Flask, render_template, abort, jsonify, request, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# مفتاح سري لحماية جلسات تسجيل الدخول (Session)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key_youssef")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- 1. مسار صفحة الزبون (الـ QR Code) ---
@app.route('/shop/<slug>')
def shop_page(slug):
    shop_response = supabase.table('shops').select('*').eq('slug', slug).execute()
    if not shop_response.data:
        abort(404)
        
    shop_data = shop_response.data[0]
    shop_id = shop_data['id']
    
    try:
        stats = supabase.table('analytics').select('scans').eq('shop_id', shop_id).execute()
        if stats.data:
            supabase.table('analytics').update({'scans': stats.data[0]['scans'] + 1}).eq('shop_id', shop_id).execute()
    except Exception as e:
        print("Analytics Error:", e)
    
    wallets_response = supabase.table('wallets').select('*').eq('shop_id', shop_id).execute()
    
    return render_template('index.html', shop=shop_data, wallets=wallets_response.data)

@app.route('/api/track-click/<shop_id>', methods=['POST'])
def track_click(shop_id):
    try:
        stats = supabase.table('analytics').select('clicks').eq('shop_id', shop_id).execute()
        if stats.data:
            supabase.table('analytics').update({'clicks': stats.data[0]['clicks'] + 1}).eq('shop_id', shop_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error"}), 500

# --- 2. مسارات لوحة التحكم (Dashboard) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        slug = request.form.get('slug')
        password = request.form.get('password')
        
        # التأكد من صحة بيانات الدخول
        response = supabase.table('shops').select('*').eq('slug', slug).eq('password', password).execute()
        
        if response.data:
            session['shop_id'] = response.data[0]['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="اسم الدخول أو كلمة المرور غير صحيحة")
            
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # منع الدخول إذا لم يسجل الدخول
    if 'shop_id' not in session:
        return redirect(url_for('login'))
        
    shop_id = session['shop_id']
    
    # معالجة إضافة رقم محفظة جديد
    if request.method == 'POST':
        new_phone = request.form.get('phone_number')
        if new_phone:
            supabase.table('wallets').insert({'shop_id': shop_id, 'phone_number': new_phone}).execute()
            return redirect(url_for('dashboard'))
            
    # جلب البيانات لعرضها في اللوحة
    shop_data = supabase.table('shops').select('*').eq('id', shop_id).execute().data[0]
    wallets = supabase.table('wallets').select('*').eq('shop_id', shop_id).execute().data
    stats = supabase.table('analytics').select('*').eq('shop_id', shop_id).execute().data[0]
    
    return render_template('dashboard.html', shop=shop_data, wallets=wallets, stats=stats)

@app.route('/delete-wallet/<wallet_id>')
def delete_wallet(wallet_id):
    if 'shop_id' not in session:
        return redirect(url_for('login'))
    
    supabase.table('wallets').delete().eq('id', wallet_id).execute()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('shop_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)