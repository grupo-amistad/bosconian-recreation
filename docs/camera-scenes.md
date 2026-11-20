# Cámara, wraparound y flujo de escenas

El mundo usa coordenadas en píxeles y toma su tamaño de `world_size` en el JSON
del nivel. `CWorldEntity` marca las entidades que se actualizan y dibujan en el
mundo. El HUD y el minimapa usan coordenadas de pantalla, por lo que no siguen a
la cámara. `system_wraparound` mantiene las posiciones dentro del mundo; la
cámara y las colisiones consideran la distancia más corta entre ambos bordes.

La partida usa una sola instancia de Pygame y un único Game Loop. `SceneManager`
cambia entre título, instrucciones, créditos, juego, pausa, continuación y
resultado. Para avanzar de nivel, el sistema que detecte que se destruyeron todas
las bases debe llamar `GameEngine.complete_level()`. El nivel 10 muestra la
victoria. Cada JSON de nivel debe declarar `world_size` y `player_spawn`.

La pausa detiene los sistemas de juego y el parpadeo/parallax de estrellas,
congela el audio y dibuja la escena de pausa sin entidades ni minimapa. Tras
perder todas las vidas aparece una ventana de continuación de cinco segundos.
Continuar reinicia el nivel con cuatro vidas y cero puntos; dejar vencer el
tiempo vuelve al menú.
