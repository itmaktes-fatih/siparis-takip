[app]
title = Siparis Takip
package.name = siparistakip
package.domain = com.mimas.siparistakip
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js
version = 1.0.0

requirements = python3,kivy,flask,openpyxl,firebase-admin,requests

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1