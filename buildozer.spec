[app]
title = Siparis Takip
package.name = siparistakip
package.domain = com.mimas.siparistakip
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Sadece Kivy ve temel ağ kütüphaneleri (firebase-admin kesinlikle YOK)
requirements = python3,kivy,requests,urllib3,certifi,chardet,idna

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

# Sadece 64-bit modern Android cihazlar için derle (Süreci %50 hızlandırır ve bellek taşmasını önler)
android.archs = arm64-v8a

# NDK ve SDK Sabit Sürümleri
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
