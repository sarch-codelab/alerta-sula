SMS CONSOLE - GUIA
===================

Envia SMS gratis desde tu PC a cualquier numero de Honduras.
Usa Email-to-SMS: un email que el carrier convierte en SMS.


COMO FUNCIONA
--------------
Cada carrier de celular tiene una direccion de email.
Si le mandas un email a 33154594@sms.tigo.hn, el usuario recibe un SMS.

No necesitas Twilio, ni API keys, ni registrar numeros.


1. CONFIGURAR GMAIL
---------------------
Necesitas una cuenta de Gmail con verificacion en 2 pasos.

1. Ande a https://myaccount.google.com/security
2. Activa verificacion en 2 pasos
3. Busca "Contraseñas de aplicacion"
4. Creas una nueva (ponele "SMS Tool")
5. Copias la contraseña de 16 caracteres


2. INSTALAR DEPENDENCIAS
-------------------------
  pip install -r requirements.txt


3. EJECUTAR
-----------
Doble clic en iniciar.bat

Selecciona 1, pon el numero, elegi el carrier, escribe el mensaje.


4. LIMITACIONES
---------------
- El carrier del destino debe soportar email-to-SMS
- Funciona con Tigo, Claro, Entel en Honduras
- No todas las empresas de celular lo soportan
- Si no funciona con un carrier, prova con otro
