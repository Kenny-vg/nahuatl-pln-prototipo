# Verificación de frases cotidianas vs GDN-UNAM

Fecha: 2-oct-2026. Hizo: Kendra (automático, para Rodrigo).
Fuente: Gran Diccionario Náhuatl UNAM (gdn.iib.unam.mx), consulta por grafía normalizada.

## Método
Se extrajeron las 111 palabras únicas del náhuatl en `datos/frases_cotidianas.csv`
(con `limpiar()`) y se buscó cada una literal en el GDN.

## Resumen
- 61/111 aparecen literales con significado que coincide con la frase. Ejemplos:
  amo=no, amoxtli=libro, atzintli=agua, axcan=hoy/ahora, calli=casa, canin=dónde,
  ce=un, cualli=bueno, hueyi=grande, huitz=venir, moztla=mañana, nehua=yo,
  nican=aquí, nochi=todo, tomin=dinero, tonalli=día, xihuitl=año, yalhua=ayer,
  yohualli=noche, tehuan=nosotros, yehuan=ellos.
- 50/111 no aparecen literales. La mayoría se explica sola y NO significa error:
  - Verbos conjugados (ti-, ni-, o-, -queh): ticochizqueh, oquipolohqueh, ticpiaz…
  - Sustantivos poseídos (mo-, no-, to-): mocihuaicnihuan, nocnihuan, tocoltzitzihuan…
  - Plurales (-tin): caltin (singular calli sí existe).
  - Préstamos del español: centavo. Nombre propio: francisco.
  - Variantes de escritura: mahtlactli (GDN: matlactli), tahtli (GDN: tachtli),
    tlahtohua (GDN: tlahtoa), quexqui/quehquich (GDN: quezqui).
- Conclusión: las 40 frases usan vocabulario real y coherente. Ninguna frase queda
  "verificada" solo con esto: falta quitar prefijos para llegar a la raíz y/o
  confirmación de hablante en los casos dudosos (lista abajo).

## Pendientes de revisión humana (no encontrados y no explicados del todo)
tahtli, tlahtohua, yah, xochimila, xochimilan, cihuacalehcapo, conte,
tlachipahtica, tlatzacualpan, ximohtalhui, zohuapa, incaltlapachol, intomin,
ipatin, maicnin, noteahui, notlacohuiz, iman, icayohua, ancateh, cateh, yezqueh.

Tabla completa palabra por palabra: ver `verif_gdn.csv` (temporal, pedírselo a Kendra).
