from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
import requests
import json
from config import FIREBASE_URL
from excel_import import read_excel

Window.clearcolor = (0.12, 0.12, 0.14, 1)

class SiparisTakipApp(App):
    def build(self):
        self.current_week = None
        self.all_jobs = {}

        self.main_layout = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # Üst Başlık
        self.header = Label(
            text="Haftalık Sipariş Takip", 
            size_hint_y=None, 
            height=40, 
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.main_layout.add_widget(self.header)

        # Üst Navigasyon / Geri Butonu Alanı
        self.nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        self.btn_back = Button(
            text="⬅️ Haftalara Dön", 
            size_hint_x=0.4, 
            background_normal='',
            background_color=(0.3, 0.3, 0.35, 1),
            bold=True
        )
        self.btn_back.bind(on_press=lambda x: self.show_weeks_screen())
        self.nav_layout.add_widget(self.btn_back)
        
        self.btn_refresh = Button(
            text="🔄 Yenile", 
            size_hint_x=0.6, 
            background_normal='',
            background_color=(0.15, 0.45, 0.85, 1),
            bold=True
        )
        self.btn_refresh.bind(on_press=lambda x: self.fetch_data_and_refresh())
        self.nav_layout.add_widget(self.btn_refresh)
        self.btn_import = Button(
            text="📂 Excel Yükle",
            size_hint_x=0.7,
            background_normal='',
            background_color=(0.15, 0.55, 0.25, 1),
            bold=True
        )

        self.btn_import.bind(on_press=self.import_excel)

        self.nav_layout.add_widget(self.btn_import)
        
        self.main_layout.add_widget(self.nav_layout)

        # Kaydırılabilir İçerik
        self.scroll = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[0, 5, 0, 5])
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        self.main_layout.add_widget(self.scroll)

        Clock.schedule_once(lambda dt: self.fetch_data_and_refresh(), 0.5)
        return self.main_layout

    def fetch_data_and_refresh(self):
        """Firebase'den verileri çeker"""
        try:
            response = requests.get(f"{FIREBASE_URL}/weekly_plan.json", timeout=10)
            if response.status_code == 200 and response.json():
                self.all_jobs = response.json()
            else:
                self.all_jobs = {}
        except Exception as e:
            print(f"Veri çekme hatası: {e}")
            self.all_jobs = {}

        if self.current_week:
            self.show_orders_screen(self.current_week)
        else:
            self.show_weeks_screen()

    # -------------------------------------------------------------
    # EKRAN 1: HAFTA SEÇİM EKRANI
    # -------------------------------------------------------------
    def show_weeks_screen(self):
        self.current_week = None
        self.header.text = "Hafta Seçiniz"
        self.btn_back.disabled = True
        self.grid.clear_widgets()

        weeks = set()
        for job_id, data in self.all_jobs.items():
            if isinstance(data, dict):
                week = data.get('week', 'Diğer')
                weeks.add(week)

        sorted_weeks = sorted(list(weeks))

        if not sorted_weeks:
            self.grid.add_widget(Label(text="Kayıtlı hafta verisi bulunamadı.", color=(0.7, 0.7, 0.7, 1)))
            return

        for week in sorted_weeks:
            btn_week = Button(
                text=f"📅  {week}",
                size_hint_y=None,
                height=60,
                background_normal='',
                background_color=(0.20, 0.22, 0.28, 1),
                font_size='17sp',
                bold=True,
                color=(0.35, 0.75, 1, 1)
            )
            btn_week.bind(on_press=lambda instance, w=week: self.show_orders_screen(w))
            self.grid.add_widget(btn_week)

    # -------------------------------------------------------------
    # EKRAN 2: SİPARİŞ LİSTESİ EKRANI (Tekil Siparişler)
    # -------------------------------------------------------------
    def show_orders_screen(self, week_name):
        self.current_week = week_name
        self.header.text = f"Siparişler ({week_name})"
        self.btn_back.disabled = False
        self.grid.clear_widgets()

        # Sipariş bazlı gruplama (Her sipariş 1 kez görünecek)
        grouped_orders = {}

        for job_id, data in self.all_jobs.items():
            if isinstance(data, dict) and data.get('week') == week_name:
                order_no = data.get('order_no', 'Tanımsız')
                if order_no not in grouped_orders:
                    grouped_orders[order_no] = {
                        "title": data.get('title', ''),
                        "status_note": data.get('status_note', ''),
                        "items": []
                    }
                grouped_orders[order_no]["items"].append((job_id, data))

        if not grouped_orders:
            self.grid.add_widget(Label(text="Bu haftaya ait sipariş bulunamadı.", color=(0.7, 0.7, 0.7, 1)))
            return

        for order_no, order_data in grouped_orders.items():
            card = BoxLayout(orientation='vertical', size_hint_y=None, padding=12, spacing=6)
            
            with card.canvas.before:
                Color(0.18, 0.20, 0.23, 1)
                card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            card.bind(pos=self._update_rect, size=self._update_rect)

            # Sipariş Başlığı
            lbl_title = Label(
                text=f"📦 Sipariş No: {order_no}",
                size_hint_y=None, height=25,
                font_size='16sp', bold=True,
                color=(1, 0.8, 0.3, 1), halign='left'
            )
            lbl_title.bind(size=lbl_title.setter('text_size'))
            card.add_widget(lbl_title)

            # İş Tanımı / Kısa Metin
            lbl_desc = Label(
                text=order_data["title"],
                size_hint_y=None, height=22,
                font_size='13sp', color=(0.8, 0.8, 0.8, 1), halign='left'
            )
            lbl_desc.bind(size=lbl_desc.setter('text_size'))
            card.add_widget(lbl_desc)

            # Mevcut Durum / Açıklama Notu Var Mı?
            note_text = f"💬 Durum Notu: {order_data['status_note']}" if order_data['status_note'] else "💬 Durum Notu: Eklenmedi"
            lbl_note = Label(
                text=note_text,
                size_hint_y=None, height=20,
                font_size='12sp', color=(0.4, 0.8, 0.5, 1) if order_data['status_note'] else (0.5, 0.5, 0.5, 1),
                halign='left'
            )
            lbl_note.bind(size=lbl_note.setter('text_size'))
            card.add_widget(lbl_note)

            # Tıklama Butonu (Detay & Açıklama Gir)
            btn_detail = Button(
                text="Detay Gör & Durum Açıklaması Yaz",
                size_hint_y=None, height=35,
                background_normal='', background_color=(0.2, 0.6, 0.4, 1),
                bold=True, font_size='12sp'
            )
            btn_detail.bind(on_press=lambda inst, o_no=order_no, o_data=order_data: self.open_order_popup(o_no, o_data))
            card.add_widget(btn_detail)

            card.height = sum(child.height for child in card.children) + 25
            self.grid.add_widget(card)

    # -------------------------------------------------------------
    # DETAY & DURUM AÇIKLAMASI EKLENEN POPUP
    # -------------------------------------------------------------
    def open_order_popup(self, order_no, order_data):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Mevcut Alt Adımlar Özet Bilgisi
        stations = [d.get('workstation', '') for j_id, d in order_data['items']]
        content.add_widget(Label(
            text=f"İstasyon Adımları: {', '.join(stations)}", 
            size_hint_y=None, height=25, font_size='12sp', color=(0.7, 0.7, 0.7, 1)
        ))

        content.add_widget(Label(
            text="İş Durumu / Açıklama Notu:", 
            size_hint_y=None, height=20, bold=True, halign='left'
        ))

        # Açıklama Yazma Kutusu
        txt_input = TextInput(
            text=order_data.get('status_note', ''),
            multiline=True,
            size_hint_y=None,
            height=90,
            background_color=(0.15, 0.15, 0.18, 1),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(txt_input)

        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_save = Button(text="Kaydet", background_normal='', background_color=(0.2, 0.7, 0.3, 1), bold=True)
        btn_cancel = Button(text="Kapat", background_normal='', background_color=(0.6, 0.2, 0.2, 1), bold=True)

        btn_layout.add_widget(btn_save)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title=f"Sipariş No: {order_no}", content=content, size_hint=(0.9, 0.5))

        def save_status_note(btn):
            new_note = txt_input.text.strip()
            # O siparişe ait tüm Firebase alt adımlarına bu notu güncelle
            for job_id, _ in order_data['items']:
                try:
                    patch_data = {"status_note": new_note}
                    requests.patch(f"{FIREBASE_URL}/weekly_plan/{job_id}.json", data=json.dumps(patch_data), timeout=5)
                except Exception as e:
                    print(f"Not kaydetme hatası: {e}")

            popup.dismiss()
            self.fetch_data_and_refresh()

        btn_save.bind(on_press=save_status_note)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def import_excel(self, instance):
    print("Excel Yükleme Yakında Aktif")

    popup = Popup(
        title="Bilgi",
        content=Label(text="Excel yükleme modülü hazırlanıyor."),
        size_hint=(0.6,0.3)
    )

    popup.open()
    
    def _update_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

if __name__ == '__main__':
    SiparisTakipApp().run()
