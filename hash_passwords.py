"""
تشفير كل كلمات السر القديمة في جدول shops مرة واحدة.
التشغيل: python hash_passwords.py  (بعد ما تحط SUPABASE_URL و SUPABASE_KEY في .env)
مش لازم تشغله: أي محل هيعمل تسجيل دخول كلمة سره هتتشفر لوحدها. ده بس عشان تخلص منهم كلهم مرة واحدة.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from werkzeug.security import generate_password_hash

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

shops = sb.table('shops').select('id, slug, password').execute().data
done = 0
for shop in shops:
    pw = shop.get('password')
    if pw and not pw.startswith(("scrypt:", "pbkdf2:")):
        sb.table('shops').update({'password': generate_password_hash(pw)}).eq('id', shop['id']).execute()
        done += 1
        print("hashed:", shop['slug'])
print(f"{done} password(s) hashed, {len(shops) - done} already hashed.")
