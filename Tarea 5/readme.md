# Tarea 5
## Juxin Xu y Lucas Poblete

## Preguntas
1. **(Item 1)** Antes de comenzar a programar, describa brevemente en su informe las similitudes y diferencias entre la tabla de rutas utilizadas para esta actividad, versus una tabla de rutas real.
> En las tablas de rutas utilizadas para esta atividad, se muestran rangos de puertos asociados a un puerto donde hacer forwarding, por otro lado, las tablas reales, guardan rangos de direcciones IP asociadas a la direccion de IP de un router donde hacer forwarding.
2. **(Item 5)** La forma en que su script recibe la información descrita deberá ser definida por usted y explicada apropiadamente en su informe. 
> primero se debe ejecutar el script con:
```
python3 cliente.py
```
> Luego, cada vez que se desee enviar un mensaje, se debe indicar la ip y puerto final junto con el mensaje siguiendo la estructura separada por ; descrito en "Simulando un mini-internet" y luego la ip y puerto de envio en los siguientes inputs:
```
IP_router_final;puerto_router_final;mensaje : 127.0.0.1;8883;hola
IP_envio;puerto_envio : 127.0.0.1;8882
```
3. **(item 8)** incluya una breve descripción en su informe sobre cómo maneja round-robin su código.
> Se crea la variable `rr = []` donde se almacenan los puertos ya visitados por el router, esta variable es pasada a la funcion `check_routes(routes_file_name: str, destination_address: tuple[str, int], rr: list[str]) -> tuple[str, int] | None`, y al leer la tabla de ruta, encuentra un puerto que tiene acceso al puerto final, primero verificara que no este en `rr`, lo añade a `rr` y entrega la direccion encontrada, ahora, si esta en `rr` y es el primer puerto encontrado, se guarda en otra varible, si esta en `rr` y no es el primer puerto encontrado, simplemente se pasa al siguiente. Cuando se hayan visitado todos los puertos y todos estaban en `rr`, se entrega simplemente el primer puerto encontrado.