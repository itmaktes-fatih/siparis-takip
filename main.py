import os
import openpyxl
import requests
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock

FIREBASE_URL = "https://siparis-takip-6046b-default-rtdb.europe-west1.firebasedatabase.app"

# Sadece filtrelenecek geçerli istasyonlar
VALID_WORKSTATIONS = [f"Y-STATK{i}" for i in range(1, 10)]

class SiparisTakipApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Üst Başlık
        header = Label(
            text="Sipariş & İş Takip Sistemi", 
            size_hint_y=None, 
            height=30, 
            font_size='18sp',
            bold=True
        )
        main_layout.add_widget(header)

        # Butonlar Ekranı (Excel Yükle & Yenile)
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        
        btn_upload = Button(text="Excel Yükle", background_color=(0.1, 0.7, 0.3, 1))
        btn_upload.bind(on_press=self.open_file_chooser)
        btn_layout.add_widget(btn_upload)

        btn_refresh = Button(text="Yenile", background_color=(0.2, 0.6, 1, 1))
        btn_refresh.bind(on_press=lambda x: self.load_jobs())
        btn_layout.add_widget(btn_refresh)

        main_layout.add_widget(btn_layout)

        # Liste Alanı
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        main_layout.add_widget(self.scroll)

        Clock.schedule_once(lambda dt: self.load_jobs(), 1)
        return main_layout

    # Dosya Seçici Penceresi (Popup)
    def open_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(path='/sdcard', filters=['*.xlsx'])
        content.add_widget(filechooser)

        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_select = Button(text="Yükle")
        btn_cancel = Button(text="İptal")
        
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title="Excel Dosyası Seçin (.xlsx)", content=content, size_hint=(0.9, 0.9))

        def load_selected_file(btn):
            if filechooser.selection:
                popup.dismiss()
                self.process_and_upload_excel(filechooser.selection[0])

        btn_select.bind(on_press=load_selected_file)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    # Excel Okuma, Süzme ve Mükerrer Temizleme Mantığı
    def process_and_upload_excel(self, file_path):
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active

            unique_records = {}
            # Excel başlıklarını atlayıp satırları tarıyoruz
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]: 
                    continue

                # Excel sütun sıralamasına göre eşleme:
                # row[0]: Sipariş No, row[1]: İstasyon/İşlem Adımı, row[2]: Açıklama/Başlık, row[3]: Hafta
                order_no = str(row[0]).strip()
                workstation = str(row[1]).strip() if len(row) > 1 else ""
                title = str(row[2]).strip() if len(row) > 2 else ""
                week = str(row[3]).strip() if len(row) > 3 else "2026-W30"

                # 1. Filtre: Sadece Y-STATK1 ile Y-STATK9 arasındaki istasyonlar
                if workstation in VALID_WORKSTATIONS:
                    # 2. Mükerrer Engelleme: Aynı Hafta + Sipariş No + İstasyon tekil anahtar yapılır
                    unique_key = f"{week}_{order_no}_{workstation}"
                    
                    unique_records[unique_key] = {
                        "order_no": order_no,
                        "workstation": workstation,
                        "title": title,
                        "week": week,
                        "status": "Bekliyor"
                    }

            # Verileri Firebase Realtime Database'e gönderme
            if unique_records:
                for record_key, payload in unique_records.items():
                    requests.patch(f"{FIREBASE_URL}/weekly_plan/{record_key}.json", data=json.dumps(payload))
                
                self.load_jobs()

        except Exception as e:
            print(f"Excel Okuma Hatası: {e}")

    # Firebase'den Listeleme
    def load_jobs(self):
        self.grid.clear_widgets()
        try:
            response = requests.get(f"{FIREBASE_URL}/weekly_plan.json", timeout=10)
            if response.status_code == 200 and response.json():
                jobs = response.json()
                count = 0
                for job_id, data in jobs.items():
                    if isinstance(data, dict):
                        card = BoxLayout(orientation='vertical', size_hint_y=None, height=110, padding=10, spacing=5)
                        
                        title_text = f"[{data.get('workstation', '-')}] Sipariş: {data.get('order_no', '-')}"
                        detail_text = f"{data.get('title', '')} | Durum: {data.get('status', 'Bekliyor')}"
                        
                        card.add_widget(Label(text=title_text, bold=True, size_hint_y=None, height=25))
                        card.add_widget(Label(text=detail_text, size_hint_y=None, height=25))

                        if data.get('status') != 'Tamamlandı':
                            btn_complete = Button(text="Tamamla", size_hint_y=None, height=35, background_color=(0, 0.8, 0.2, 1))
                            btn_complete.bind(on_press=lambda btn, j_id=job_id: self.complete_job(j_id))
                            card.add_widget(btn_complete)

                        self.grid.add_widget(card)
                        count += 1

                if count == 0:
                    self.grid.add_widget(Label(text="İş kaydı bulunamadı.", size_hint_y=None, height=40))
        except Exception as e:
            self.grid.add_widget(Label(text=f"Bağlantı Hatası: {str(e)}", size_hint_y=None, height=50))

    def complete_job(self, job_id):
        try:
            patch_data = {"status": "Tamamlandı"}
            requests.patch(f"{FIREBASE_URL}/weekly_plan/{job_id}.json", data=json.dumps(patch_data), timeout=5)
            self.load_jobs()
        except Exception as e:
            print(f"Güncelleme hatası: {e}")

if __name__ == '__main__':
    SiparisTakipApp().run()
