# Diagrama de flujo del proxy

```mermaid
flowchart TB
  subgraph C[" Cliente "]
    direction LR
    c1(["socket() + connect()"]) --> c2(["send()"]) --> c3(["recv() + close()"])
  end

  subgraph P[" Proxy "]
    direction LR
    p1(["socket() + bind() + listen()  #1"]) --> p2(["accept() -> #2"])
    p2 --> p3(["recv() #2 en bucle<br/>extrae host y puerto"])
    p3 --> pd{"bloqueado?"}
    pd -- "si" --> pb(["send() #2: 403 + HTML"])
    pd -- "no" --> p4(["socket() + connect() + send()  #3<br/>agrega X-ElQuePregunta"])
    p4 --> p5(["recv() #3 en bucle<br/>censura + Content-Length"])
    p5 --> p6(["send() #2"])
    p6 --> p7(["close() #2 y #3"])
    pb --> p7
  end

  subgraph S[" Servidor final "]
    direction LR
    s1(["socket() + bind()<br/>listen() + accept()"]) --> s2(["recv() + send()"])
  end

  c2 -- "peticion" --> p3
  p4 -- "peticion + X-ElQuePregunta" --> s2
  s2 -- "respuesta" --> p5
  p6 -- "respuesta censurada" --> c3
  pb -- "403" --> c3
```

Los numeros #1, #2 y #3 son los tres sockets del proxy:

- **#1 socket de escucha**: bind + listen, nunca transfiere datos, vive todo el programa
- **#2 socket con el cliente**: lo devuelve accept(), el proxy actua como servidor
- **#3 socket con el servidor final**: el proxy actua como cliente, se crea y cierra por cada peticion

Al cerrar #2 y #3 el proxy vuelve a accept() para atender al siguiente cliente.
