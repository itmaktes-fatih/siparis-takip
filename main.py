from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import requests
import json

# Tam ve Doğruluk Kazanan Realtime Database Adresiniz
FIREBASE_URL = "https://siparis-takip-6046b-default-rtdb.europe-west1.firebasedatabase.app"

class SiparisTakipApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Başlık Alanı
        header = Label(
            text="Sipariş & İş Takip Sistemi", 
            size_hint_y=None, 
            height=40, 
            font_size='18sp',
            bold=True
        )
        main_layout.add_widget(header)

        # Yenile Butonu
        btn_refresh = Button(
            text="İş Listesini Yenile", 
            size_hint_y=None, 
            height=45,
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_refresh.bind(on_press=lambda x: self.load_jobs())
        main_layout.add_widget(btn_refresh)

        # Kaydırılabilir İçerik Alanı
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        main_layout.add_widget(self.scroll)

        Clock.schedule_once(lambda dt: self.load_jobs(), 1)
        return main_layout

    def load_jobs(self):
        self.grid.clear_widgets()
        try:
            # Firebase Realtime Database üzerinden verileri çekiyoruz
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
            else:
                self.grid.add_widget(Label(text="Henüz veri yok veya bağlantı bekleniyor.", size_hint_y=None, height=40))

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
