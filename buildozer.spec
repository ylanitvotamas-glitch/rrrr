[app]
title = MyGame
package.name = mygame
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,wav,ogg,ttf
version = 0.1
requirements = python3==3.11.5,hostpython3==3.11.5,pygame
orientation = landscape
fullscreen = 1
android.permissions =
android.accept_sdk_license = True
android.api = 33
android.ndk = 25b
android.ndk_api = 21
p4a.branch = v2024.01.21
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
