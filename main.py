import os
from flask import Flask, render_template, request, jsonify
import openpyxl
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# ---------------------------------------------------------
# 1. FIREBASE BAĞLANTISI
# ---------------------------------------------------------
FIREBASE_KEY_PATH = "firebase_key.json"

if os.path.exists(FIREBASE_KEY_PATH):
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    print(f"HATA: '{FIREBASE_KEY_PATH}' dosyası bulunamadı!")

# Sadece Y-STATK1 ile Y-STATK9 arasındaki İşlem İş yerlerini kabul ediyoruz
VALID_WORKSTATIONS = [f"Y-STATK{i}" for i in range(1, 10)]

# ---------------------------------------------------------
# 2. ANA SAYFA
# ---------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------------------------------
# 3. SEÇİLİ HAFTANIN İŞLERİNİ GETİR
# ---------------------------------------------------------
@app.route('/api/get-week-jobs', methods=['GET'])
def get_week_jobs():
    selected_week = request.args.get('week', '2026-W30')
    
    try:
        jobs_ref = db.collection('weekly_plan').where('week', '==', selected_week)
        docs = jobs_ref.stream()
        
        jobs_list = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            jobs_list.append(data)
            
        return jsonify({'status': 'success', 'jobs': jobs_list}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------------------------------------------------------
# 4. EXCEL YÜKLEME VE İŞLEM İŞYERİ FİLTRELEME
# ---------------------------------------------------------
@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    try:
        selected_week = request.form.get('week')
        file = request.files.get('excel')
        
        if not file or not selected_week:
            return jsonify({'status': 'error', 'message': 'Eksik dosya veya hafta seçimi!'}), 400

        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb.active

        headers = [str(cell.value).strip() if cell.value else '' for cell in sheet[1]]
        
        required_cols = ['Öncelik', 'Sipariş No', 'Bildirim No', 'Kısa Metin', 'İşlem İşyeri', 'Başlama Tarihi']
        col_indices = {}
        
        for col_name in required_cols:
            if col_name in headers:
                col_indices[col_name] = headers.index(col_name)
            else:
                return jsonify({'status': 'error', 'message': f"Excel'de eksik sütun: {col_name}"}), 400

        unique_jobs = {}
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            
            # 1. İŞLEM İŞYERİ FİLTRESİ (Y-STATK1 - Y-STATK9 Kontrolü)
            workstation_val = str(row[col_indices['İşlem İşyeri']]).strip().upper() if row[col_indices['İşlem İşyeri']] is not None else ''
            
            # Eğer İşlem İşyeri Y-STATK1...Y-STATK9 arasında DEĞİLSE atla!
            if workstation_val not in VALID_WORKSTATIONS:
                continue

            # 2. HAFTA İÇİ MÜKERRER ELEME (Teke Düşürme)
            order_no = str(row[col_indices['Sipariş No']]) if row[col_indices['Sipariş No']] is not None else '-'
            notif_no = str(row[col_indices['Bildirim No']]) if row[col_indices['Bildirim No']] is not None else '-'
            
            unique_key = order_no if order_no != '-' else notif_no
            
            if unique_key not in unique_jobs and unique_key != '-':
                priority = str(row[col_indices['Öncelik']]) if row[col_indices['Öncelik']] is not None else 'Normal'
                title = str(row[col_indices['Kısa Metin']]) if row[col_indices['Kısa Metin']] is not None else ''
                
                raw_date = row[col_indices['Başlama Tarihi']]
                start_date = str(raw_date)[:10] if raw_date is not None else ''

                unique_jobs[unique_key] = {
                    'week': selected_week,
                    'priority': priority,
                    'order_no': order_no,
                    'notification_no': notif_no,
                    'title': title,
                    'workstation': workstation_val,
                    'start_date': start_date,
                    'assigned_team': 'Atanmadı',
                    'status': 'Bekliyor'
                }

        # Firebase Batch Kayıt
        batch = db.batch()
        for key, job_data in unique_jobs.items():
            doc_id = f"{selected_week}_{key}"
            doc_ref = db.collection('weekly_plan').document(doc_id)
            batch.set(doc_ref, job_data)
            
        batch.commit()
        return jsonify({'status': 'success', 'message': f'Filtreye uygun {len(unique_jobs)} adet ana iş yüklendi.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------------------------------------------------------
# 5. İŞ GÜNCELLEME API
# ---------------------------------------------------------
@app.route('/api/update-job', methods=['POST'])
def update_job():
    try:
        data = request.json
        job_id = data.get('job_id')
        new_status = data.get('status')
        assigned_team = data.get('assigned_team')

        if not job_id:
            return jsonify({'status': 'error', 'message': 'İş ID gereklidir!'}), 400

        doc_ref = db.collection('weekly_plan').document(job_id)
        
        update_data = {}
        if new_status:
            update_data['status'] = new_status
        if assigned_team:
            update_data['assigned_team'] = assigned_team
            if new_status != 'Tamamlandı':
                update_data['status'] = 'Atandı'

        doc_ref.update(update_data)
        return jsonify({'status': 'success', 'message': 'İş güncellendi.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)