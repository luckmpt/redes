# Tarea 5
## Juxin Xu y Lucas Poblete

## Anotaciones de Mini-Internet sin TTL
1. **(Item 1)** Antes de comenzar a programar, describa brevemente en su informe las similitudes y diferencias entre la tabla de rutas utilizadas para esta actividad, versus una tabla de rutas real.
> En las tablas de rutas utilizadas para esta atividad, se muestran rangos de puertos asociados a un puerto donde hacer forwarding, por otro lado, las tablas reales, guardan rangos de direcciones IP asociadas a la direccion de IP de un router donde hacer forwarding.
2. **(Item 5)** La forma en que su script recibe la información descrita deberá ser definida por usted y explicada apropiadamente en su informe. 
> primero se debe ejecutar el script con:
>```
>python3 cliente.py
>```
> Luego, cada vez que se desee enviar un mensaje, se debe indicar la ip y puerto final junto con el mensaje siguiendo la estructura separada por ; descrito en "Simulando un mini-internet" y luego la ip y puerto de envio en los siguientes inputs:
>```
>IP_router_final;puerto_router_final;mensaje : 127.0.0.1;8883;hola
>IP_envio;puerto_envio : 127.0.0.1;8882
>```
3. **(item 8)** incluya una breve descripción en su informe sobre cómo maneja round-robin su código.
> Se crea la variable `rr = []` donde se almacenan los puertos ya visitados por el router, esta variable es pasada a la funcion `check_routes(routes_file_name: str, destination_address: tuple[str, int], rr: list[str]) -> tuple[str, int] | None`, y al leer la tabla de ruta, encuentra un puerto que tiene acceso al puerto final, primero verificara que no este en `rr`, lo añade a `rr` y entrega la direccion encontrada, ahora, si esta en `rr` y es el primer puerto encontrado, se guarda en otra varible, si esta en `rr` y no es el primer puerto encontrado, simplemente se pasa al siguiente. Cuando se hayan visitado todos los puertos y todos estaban en `rr`, se entrega simplemente el primer puerto encontrado.
4. **(Item 9)** ¿En que posición (línea) de la tabla debería ir la ruta default? Añada en su informe cómo queda su nueva tabla de rutas y la respuesta a esta pregunta.
> En las ultimas dos lineas de cada una de las otras tablas, se agrega el envio al puerto 7000 para rangos entre [0, 8879] y [8887, 65535].
>```
>...
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>```
## Pruebas Mini-Internet sin TTL
1. pruebe qué ocurre si alguien configura mal una de las tablas de rutas y coméntelo brevemente en su informe.
> Si se configura mal una tabla de rutas, como en el caso del ejemplo que los mensajes que van hacia `R3` y llegan a `R1`y `R2`, sus tablas de rutas los redirijen a `R25. pruebe qué ocurre si alguien configura mal una de las tablas de rutas y coméntelo brevemente en su informe.
> Si se configura mal una tabla de rutas, como en el caso del ejemplo que los mensajes que van hacia `R3` y llegan a `R1` y `R2`, sus tablas de rutas de cada uno los redirijen a `R2` y `R1` respectivamente, esto provoca que el mensaje este saltando entre ambos routers infinitamente, provocando un bucle sin fin en ambos routers. Es decir, el mensaje pasa a estar perdido en la red sin nunca llegar a su destino.
2. Usando las rutas de la estructura de 5 routers, pruebe su código enviando paquetes a R1 con destino R5 y vea que su función de rutas efectivamente usa round-robin, es decir, va alternando entre rutas. Haga varias pruebas ¿cuántos saltos dan los paquetes? ¿siempre dan la misma cantidad de saltos?¿cómo se compara la cantidad de saltos que dan los paquetes versus la cantidad de saltos mínima? Anote sus observaciones en el informe.
> Si hace correctamente round robin, pues en la primera prueba, `R2` el paquete llega 3 veces, y las tres veces fueron redirijidos a un router distinto.
>
> En el primer test, el paquete dio 7 saltos, en el segundo test el paquete dio 3 saltos, por lo que no siempre dan la misma cantidad de saltos.
>
> La cantidad de saltos minima son 3 saltos, que fue justamente el resultado del segundo test, sin embargo, el primer test realizo 7 saltos, que es mas del doble.
3. Repita las pruebas del punto 2 utilizando la estructura que se le pidió crear en el test 2 del paso 8 y escriba sus observaciones en su informe. Añada en su informe los contenidos de los distintos archivos de rutas que debió crear.
> En el primer test, el paquete dio 9 saltos, en el segundo test el paquete dio 5 saltos, en el tercero dio 7 saltos. Por lo que no se repiten la cantidad de saltos y se alejan bastante de la cantidad minima que siguen siendo 3. Los aarchivos de ruta nuevos son los siguientes:
>```
># rutas_R0_v4.txt
>
>127.0.0.1/24 8881 8886 127.0.0.1 8881
>127.0.0.1/24 8881 8886 127.0.0.1 8882
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R1_v4.txt
>
>127.0.0.1/24 8882 8886 127.0.0.1 8882
>127.0.0.1/24 8882 8886 127.0.0.1 8880
>127.0.0.1/24 8880 8880 127.0.0.1 8882
>127.0.0.1/24 8880 8880 127.0.0.1 8880
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R2_v4.txt
>
>127.0.0.1/24 8880 8881 127.0.0.1 8881
>127.0.0.1/24 8880 8881 127.0.0.1 8880
>127.0.0.1/24 8883 8886 127.0.0.1 8883
>127.0.0.1/24 8883 8886 127.0.0.1 8884
>127.0.0.1/24 8883 8886 127.0.0.1 8886
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R3_v4.txt
>
>127.0.0.1/24 8880 8882 127.0.0.1 8882
>127.0.0.1/24 8880 8882 127.0.0.1 8885
>127.0.0.1/24 8884 8886 127.0.0.1 8882
>127.0.0.1/24 8884 8886 127.0.0.1 8885
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R4_v4.txt
>
>127.0.0.1/24 8880 8883 127.0.0.1 8882
>127.0.0.1/24 8880 8883 127.0.0.1 8885
>127.0.0.1/24 8885 8886 127.0.0.1 8882
>127.0.0.1/24 8885 8886 127.0.0.1 8885
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R5_v4.txt
>
>127.0.0.1/24 8881 8884 127.0.0.1 8884
>127.0.0.1/24 8881 8884 127.0.0.1 8883
>127.0.0.1/24 8886 8886 127.0.0.1 8884
>127.0.0.1/24 8886 8886 127.0.0.1 8883
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R6_v4.txt
>
>127.0.0.1/24 8880 8885 127.0.0.1 8882
>127.0.0.1/24 8880 8885 127.0.0.1 8883
>127.0.0.1/24 0 8879 127.0.0.1 7000
>127.0.0.1/24 8887 65535 127.0.0.1 7000
>
># rutas_R6_v4.txt
>
>
>```
