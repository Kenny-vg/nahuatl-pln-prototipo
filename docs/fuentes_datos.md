# Fuentes de datos del prototipo

## Corpus base: Axolotl (ya integrado en `train_80%.csv`)
- Dataset: `somosnlp-hackathon-2022/Axolotl-Spanish-Nahuatl`, licencia MPL-2.0.
- Cita: Gutierrez-Vasques, Sierra y Pompa, "Axolotl: a web accessible parallel
  corpus for spanish-nahuatl".
- Contenido mayoritario: Biblia (opus-bible-uedin, ~42%) y crónicas coloniales
  s. XVI–XVII. Dominio histórico/religioso, varias ortografías y dialectos.

## Ampliación moderna: Tatoeba (`datos/extra_moderno.csv`, 369 pares)
- Origen: API Tatoeba v1 (`/v1/sentences?lang=nch,ngu,nlv,nah&showtrans:lang=spa`,
  paginación por cursor), octubre 2026.
- Variantes: `nah` genérico (234), huasteca-centro `nch` (71), guerrero `ngu` (61),
  orizaba `nlv` (7). Frases cortas contemporáneas (mediana 23 caracteres en español).
- Licencia: **CC BY 2.0 FR** (requiere atribución; ver columna `fuente` con id Tatoeba).
- Método: pares directos es↔nah con traducción al español; deduplicados contra el
  train por forma normalizada (`limpiar()`); 4/373 ya existían y se descartaron.
- Efecto medido: `Hola amigo` (no encontrada → sim 0.88 + literal `niltze nomaicnin`),
  `Hola` → `niltze`, `Flor y corazón` → literal con `noyollo` (antes partícula `ca`),
  `computadora` ahora se recupera (tepoz/chīuhpōhualhuaz) y salió de la lista de
  palabras desconocidas en `pruebas/test_modelo.py`.
- Estado: traducido por colaboradores (nativos en su mayoría), **pendiente de
  validación por hablante**; muestra de 30 en `docs/muestra_verificacion_tatoeba.csv`.

## Evaluada y diferida: AmericasNLI-nah
- 376 dev + 738 test pares, traducciones expertas de XNLI-es conversacional
  (cara a cara/cartas/teléfono), huasteco normalizado al clásico. Ideal en teoría.
- **No integrada:** el dump público (`nala-cub/americas_nli`, CC-BY-SA 4.0) trae solo
  columnas `premise/hypothesis/label` en náhuatl, sin IDs de unión con XNLI-es;
  el join posicional se refutó (falla desde la fila 100). Forzar pares desalineados
  envenenaría el modelo, así que se difiere hasta hallar el mapeo oficial.
- Referencia: Ebrahimi et al. 2022, "AmericasNLI" (ACL long).

## Pendiente (para Rodrigo a su regreso)
- Adjudicación dialectal fina de `extra_moderno.csv` y confirmación de hablante.
- Constitución mexicana en náhuatl (INALI) y JW300-nah como fase 2 de volumen.
