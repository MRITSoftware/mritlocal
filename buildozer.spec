[app]
title = MRIT Tuya Gateway
package.name = mritgateway
package.domain = com.mritsoftware
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy,tinytuya
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1

[buildozer]
log_level = 2
warn_on_root = 1

[android]
permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
api = 30
minapi = 21
p4a.branch = master
android.allow_backup = True
android.archs = arm64-v8a,armeabi-v7a

