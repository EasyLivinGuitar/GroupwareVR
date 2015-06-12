========================
   Start PS-Tracking
========================

$ sudo /opt/local/bin/pstrack2configure eth0
$ /opt/local/bin/pstrack2start
- in tab "interface", group "dtrack": check enable, set "Client1 address" adress to "127.0.0.1" and port to "5020"

=========================================
   Latus Demon aktualisieren
=========================================

$ cp ./libavango_polhemus.so /opt/avang/new_renderer/lib/libavango_polhemus.so

================================================
    Start Daemon for Polhemus Latus
================================================
$ cd /opt/avango/new_renderer/examples/polhemus; sudo /opt/avango/new_renderer/examples/polhemus/start.sh

im start skript sollte kein weiterer demon sein
- start skript ausführen


==================================
   Latus Terminal ausführen
==================================

$ cp ./LatusTerminal /opt/avango/new_renderer/lib/LatusTerminal
$ sudo /opt/avango/new_renderer/lib/LatusTerminal


================
Latus scharfschalten
================

$ sudo /opt/avango/new_renderer/examples/polhemus/polhemus-loader.sh

