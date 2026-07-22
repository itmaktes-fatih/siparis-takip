import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

import firebase_admin
from firebase_admin import credentials, firestore

# Y-STATK1 ile Y-STATK9 arasındaki adımları geçerli sayıyoruz
VALID_WORKSTATIONS = [f"Y-STATK{i}" for i in range(1, 10)]

class SiparisTakipApp(App):
    def build(self):
        self.db = None
        self.init_firebase()

        # Ana Düzen (Dikey)
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Üst Başlık
        header = Label(
            text="Sipariş & İş Takip Sistemi", 
            size_hint_y=None, 
            height=50, 
            font_size='20sp',
            bold=True
        )
        main_layout.add_widget(header)

        # Yenile Butonu
        btn_refresh = Button(
            text="İş Listesini Yenile", 
            size_hint_y=None, 
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_refresh.bind(on_press=lambda x: self.load_jobs())
        main_layout.add_widget(btn_refresh)

        # Kaydırılabilir Liste Alanı
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        main_layout.add_widget(self.scroll)

        # İlk Açılışta Verileri Yükle
        Clock.schedule_once(lambda dt: self.load_jobs(), 1)

        return main_layout

    def init_firebase(self):
        key_path = "firebase_key.json"
        if os.path.exists(key_path):
            try:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
            except Exception as e:
                print(f"Firebase Bağlantı Hatası: {e}")

    def load_jobs(self):
        self.grid.clear_widgets()
        if not self.db:
            self.grid.add_widget(Label(text="Firebase Bağlantısı Yok!", size_hint_y=None, height=40))
            return

        try:
            # Seçili haftanın verilerini Firebase'den çekiyoruz
            docs = self.db.collection('weekly_plan').where('week', '==', '2026-W30').stream()
            
            count = 0
            for doc in docs:
                data = doc.to_dict()
                doc_id = doc.id
                
                # Kart Tasarımı
                card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=8, spacing=5)
                
                title_text = f"[{data.get('workstation', '-')}] Sipariş: {data.get('order_no', '-')}"
                detail_text = f"{data.get('title', '')} | Durum: {data.get('status', 'Bekliyor')}"
                
                card.add_widget(Label(text=title_text, bold=True, size_hint_y=None, height=25))
                card.add_widget(Label(text=detail_text, size_hint_y=None, height=25))

                # İş Bittiğinde Tamamla Butonu
                if data.get('status') != 'Tamamlandı':
                    btn_complete = Button(
                        text="Tamamla", 
                        size_hint_y=None, 
                        height=35, 
                        background_color=(0, 0.8, 0.2, 1)
                    )
                    btn_complete.bind(on_press=lambda btn, j_id=doc_id: self.complete_job(j_id))
                    card.add_widget(btn_complete)

                self.grid.add_widget(card)
                count += 1

            if count == 0:
                self.grid.add_widget(Label(text="Bu haftaya ait filtrelenmiş iş bulunamadı.", size_hint_y=None, height=40))

        except Exception as e:
            self.grid.add_widget(Label(text=f"Hata: {str(e)}", size_hint_y=None, height=40))

    def complete_job(self, job_id):
        if self.db:
            self.db.collection('weekly_plan').document(job_id).update({'status': 'Tamamlandı'})
            self.load_jobs()

if __name__ == '__main__':
    SiparisTakipApp().run()
