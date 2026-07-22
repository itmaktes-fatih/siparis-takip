[app]
title = Siparis Takip
package.name = siparistakip
package.domain = com.mimas.siparistakip
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Ağır C bağımlılıkları çıkardı, saf Python kütüphaneleri kaldı
requirements = python3,kivy==2.2.1,requests,urllib3,certifi,chardet,idna

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.1
fullscreen = 0
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
