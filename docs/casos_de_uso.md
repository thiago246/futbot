 # Casos de uso:

## Gestión del usuario:

### Caso de uso 1: Registro.  
Actor primario: Actor Externo.  
Escenario exitoso principal:  
    1. El actor selecciona la opción "registrarse".  
    2. El sistema muestra el formulario de registro (nombre de usuario, email, contraseña).  
    3. El actor completa el formulario y confirma el registro.  
    4. El sistema valida los datos ingresados, verifica que el email no esté ya registrado, crea la cuenta y confirma el registro.  
Escenarios excepcionales:  
    4.a El email ya está registrado  
     El sistema muestra un mensaje de error indicando que el email ya está en uso y solicita al actor que ingrese otro.  
    4.b Los datos ingresados son inválidos  
     El sistema muestra un mensaje de error señalando qué campos deben corregirse y vuelve a mostrar el formulario.  

### Caso de Uso 2: Login  
Actor Primario: Actor Externo 
Escenario exitoso principal:  
	1. El Actor Externo ingresa su usuario y contraseña.  
	2. El sistema verifica que sean correctos y deja que inicie sesión.  
Escenario excepcional:  
	2a. El usuario no existe o la contraseña ingresada es incorrecta.  
      * El sistema muestra un mensaje de error indicando que el usuario no existe o la contraseña es incorrecta.  
      

### Caso de uso 3: Editar contraseña.  
Actor primario: Usuario.  
Precondición: Usuario valido.  
Escenario exitoso:  
	1. El usuario ingresa a su perfil.  
	2. El sistema abre el menú del perfil.  
	3. El usuario aprieta la opción de editar contraseña.  
	4. El sistema abre un menú indicando al usuario como cambiar su contraseña.  
	5. El usuario ingresa su vieja contraseña y su nueva contraseña.  
	6. El sistema verifica los datos y actualiza la contraseña.  
Escenarios excepcionales:  
	6. a) La contraseña vieja es incorrecta.  
		- Se le pide al usuario que ingrese su vieja contraseña nuevamente y no lo deja avanzar.  
	6. b) La nueva contraseña no cumple con el mínimo de requisitos para que sea segura.  
		- El sistema le indica al usuario qué tipo de caracteres le faltan para que su contraseña sea válida.  

### Caso de uso 4: Editar foto de perfil  
Actor primario: Usuario.  
Precondición: Ninguna.  
Escenario exitoso principal:  
    1. El usuario abre su perfil y selecciona la opción “Editar perfil”.  
    2. El sistema abre un ‘formulario’ disponible para editar.  
    3. El usuario selecciona “Editar foto de perfil”.  
    4. El sistema abre un menú de avatares predefinidos.  
    5. El usuario selecciona uno.  
    6. El sistema lo agrega al formulario.  
Escenarios excepcionales:   
	Ninguno.  

### Caso de uso 5: Cerrar sesión.  
Actor primario: Usuario.  
Precondición: El usuario tiene una cuenta y la sesión iniciada.  
Escenario exitoso principal:  
        1.  El usuario selecciona la opción “Cerrar sesión”  
        2. El sistema finaliza la sesión activa del usuario.  
        3. El sistema redirige al usuario a la pantalla de inicio de sesión.  
Escenarios excepcionales:  
Ninguno.  

### Caso de uso 6: Eliminar una cuenta.  
Actor primario: Usuario.  
Precondición: El usuario tiene una cuenta y la sesión iniciada.  
Escenario exitoso principal:  
    1. El usuario selecciona la opción "eliminar cuenta".  
    2. El sistema solicita confirmación (reingresar la contraseña).  
    3. El usuario confirma que desea eliminar la cuenta.  
    4. El sistema valida la confirmación, elimina la cuenta y cierra la sesión del usuario.  
Escenarios excepcionales:  
    4.a La información ingresada es incorrecta (contraseña errónea).  
        - El sistema muestra un mensaje de error y no elimina la cuenta.  
    4.b El usuario cancela la acción antes de confirmar.  
        - El sistema cancela la operación y vuelve a la pantalla anterior sin eliminar la cuenta.  


## Gestión del club y jugadores:

### Caso de uso 7: Creación de club.  
Actor primario: Usuario.
Escenario exitoso principal:  
    1. El usuario ingresa el nombre del equipo.  
    2. El sistema valida que el nombre cumpla los requisitos.  
    3. El sistema crea el club y lo asigna permanentemente a la cuenta del usuario.  
    4. El sistema notifica la creación del equipo.  
Escenarios excepcional:  
    1.a El nombre ingresado no está disponible o no es válido.  
	    - El sistema notifica esto al usuario  


### Caso de uso 8: Creación de jugador.  
Actor primario: Usuario.  
Precondición: El usuario tiene una cuenta de FutBot con la sesión iniciada.  
Escenario exitoso principal:  
	1. 	El usuario selecciona la opción “crear jugador”  
	2.	El usuario ingresa un nombre para el jugador y distribuye los valores de PACSS.  
	3. 	El sistema valida que cada valor esté  entre 20 y 100, y que la suma total sea  exactamente 300.  
	4. 	El sistema crea al jugador y lo asocia a la cuenta de usuario.  
Escenarios excepcionales:  
	3.a  Algún valor está fuera del rango o la suma da distinto de 300.  
        - El sistema rechaza la creación del jugador con un mensaje que dice “selección de atributos inválida”.	 

### Caso de uso 9: Eliminación de jugador
Actor primario: Usuario.  
Precondición: Tiene que haber al menos un jugador creado.  
Escenario exitoso principal:  
    1. El usuario busca un jugador.  
    2. El sistema abre el panel con la informacion del jugador.  
    3. El usuario selecciona "Eliminar jugador".  
    4. El sistema elimina el jugador.  
Escenarios excepcionales:  
    3.a El jugador esta en un equipo en una liga que ya empezo.  
        - El sistema muestra un mensaje que el jugador esta en uso.  
    3.b El jugador esta jugando un partido amistoso actualmente.  
        - El sistema muestra un mensaje que el jugador esta en uso.


### Caso de uso 10: Seleccionar plantilla.  
Actor primario: Usuario.  
Precondición: El usuario debe haber creado al menos 6 jugadores.  
Escenario exitoso principal:  
    1.   El usuario selecciona la opción “elegir formación”.  
    2.   El sistema muestra al usuario los jugadores disponibles.  
    3.   El usuario selecciona exactamente 6 jugadores: 3 titulares y 3 suplentes.  
    4.   El usuario selecciona la formacion de la plantilla..  
    5.   El sistema valida la seleccion.
    6.   El sistema crea la nueva plantilla para el club. 
Escenarios excepcionales:  
    3.a  El usuario selecciona menos de 6 jugadores o más, o no respeta la distribución de titulares y suplentes.  
        - El sistema devuelve un mensaje de error “selección inválida”.
    4.a  El usuario no selecciono una formacion.
        - El sistema devuelve un mensaje de error "Se necesita seleccionar una formacion para el equipo".

### Caso de uso 11: Ver perfil de club.  
Actor Primario: Usuario.  
Precondición: Tener un perfil creado e iniciada la sesión.  
Escenario exitoso principal:  
    1. El usuario solicita ver su perfil.  
    2. El sistema abre un panel con la informacion del usuario y del club.  
Escenario exepcional:  
    Ninguno.  


### Caso de uso 12: Ver plantilla del club.  
Actor Primario: Usuario.  
Precondicion: Ninguna.  
Escenario exitoso principal:  
    1. El usuario va a la seccion "Club" y selecciona la opcion "Ver plantilla".  
    2. El sistema muestra al usuario una plantilla detallada donde se indican los PACCS y el comportamiento actual de cada jugador.  
Escenario excepcional:  
	Ninguno.



## Gestión de comportamientos:

### Caso de uso 13: Creación de comportamiento.  
Actor Primario: Usuario.  
Precondicion: Usuario valido y registrado.  
Escenario exitoso:  
	1. El usuario hace click en la opcion de crear comportamiento.  
	2. El sistema abre el menu donde el usuario puede escribir el codigo de su nuevo comportamiento.  
	3. El usuario ingresa un nombre para su comportamiento.  
	4. El sistema verifica que ese nombre no este en uso por el usuario.  
	5. El usuario escribe el codigo y le da a terminar.  
	6. El sistema verifica que el codigo sea valido (que cumpla los requisitos para que un jugador "haga algo" dentro del campo de juego) y lo guarda en la lista de comportamientos del usuario.  
Escenarios excepcionales:  
	4.a) El usuario posee un comportamiento con el mismo nombre del que quiere crear.  
		- El sistema le pide al usuario cambiar el nombre y no lo deja continuar.  
	6.a) El codigo del usuario no cumple los requisitos para que un jugador juegue correctamente.  
		- Se le manda al usuario a editar el codigo hasta que cumpla los requisitos.  

### Caso de uso 14: Validación de comportamiento.  
Actor primario: Usuario.  
Precondición: Existe al menos un comportamiento.  
Escenario exitoso principal:  
    1. El usuario selecciona la opción "validar comportamiento" sobre un comportamiento propio.  
    2. El sistema analiza el código del comportamiento, confirma que el comportamiento es válido y lo marca como disponible para asignar a un jugador.  
Escenarios excepcionales:  
    2.a El código tiene errores de sintaxis o usa funciones no permitidas.  
        - El sistema rechaza la validación y muestra un mensaje de error.  

### Caso de uso 15: Edición de comportamiento
Actor principal: Usuario  
Precondición: 
    El comportamiento seleccionado no debe de estar siendo utilizado en ese momento  
Escenario principal:  
1. El usuario accede al código del comportamiento  
2. El usuario modifica parte de ese código  
3. El usuario aprieta el botón “validar cambios”  
4. El sistema lo valida y lo deja disponible para su uso  
Escenario alternativo:  
3a. El nuevo código no es validado por el sistema.  
    - El sistema le notifica al usuario la parte que está generando conflicto.  
    - El usuario repite el paso 2 hasta que el sistema valide el comportamiento.  

### Caso de uso 16: Eliminación de comportamiento
Actor primario: Usuario.  
Precondición: EL comportamiento no esta en uso en una liga o partido amistoso.  
Escenario exitoso principal:  
1. El usuario busca el comportamiento en la lista de comportamientos.  
2. El sistema abre el código con las opciones “editar” y “eliminar”.  
3. El usuario selecciona la opción de “eliminar”.  
4. El sistema elimina el comportamiento.  
Escenarios excepcionales:  
Ninguno.  


### Caso de uso 17: Realizar cambio de comportamiento

Actor Primario: Usuario  
Precondición: Estar en un Partido activo o por arrancar. Tener comportamientos para cambiar  
Escenario existoso principal:  
    1. El usuario selecciona el jugador al que le quiere cambiar el comportamiento, antes del partido o durante el mismo  
    2. El sistema muestra el comportamiento actual del jugador y la lista de comportamientos asignables al mismo  
    3. El usuario selecciona de la lista un comportamiento distinto al actual  
    4. El sistema asigna el comportamiento al jugador  
    5. El sistema confirma el cambio al usuario y actualiza en tiempo real el partido  
Escenario alternativo:  
    4.a Que el partido finalice en medio del cambio y no se pueda concretar


### Caso de uso 18: Asignar comportamiento a un jugador.  
Actor primario: Usuario.  
Precondición: Existe al menos un comportamiento.  
Escenario exitoso principal:  
El usuario selecciona un jugador.
El sistema abre el panel con la información de un jugador.  
El usuario selecciona la opción de asignar comportamiento.  
El sistema abre un menú de comportamientos disponibles.  
El usuario selecciona el comportamiento.  
El sistema carga el comportamiento al jugador.  
Escenarios excepcionales:   
	Ninguno.  


## Gestión de ligas:

### Caso de Uso 19: Creación de liga pública  
Actor Primario: Usuario  
Escenario exitoso principal:  
    1. El usuario ingresa el nombre, cantidad de equipos, duración.  
    2. El sistema crea la liga e informa al usuario que se creó la liga con éxito.  
Escenario excepcional:  
	1a. El usuario ingresa un atributo fuera de los parámetros.  
	 *. El sistema informa que debe cambiar el atributo que ingresó mal.  



### Caso de uso 20: Creación de liga privada
Actor primario: Usuario  
Precondición: Tener una sesión iniciada.  
Escenario exitoso principal:   
    1. El usuario solicita crear una liga.     
    2. El sistema le muestra el menu de cracion de liga.  
    3. El usuario ingresa los datos (nombre, contraseña, cantidad de clubes) de la liga   
    4. El sistema valida los datos, crea la liga y marca al usuario como administrador de la misma.  
Escenario alternativo:  
    4.a Que el nombre ya esté en uso.  
    4.b Que la contraseña esté vacía.  
    4.c Que la cantidad de clubes sea menor a 3.  



### Caso de uso 21: Buscar/listar ligas.  
Actor primario: Usuario.  
Precondición: El usuario tiene una cuenta de FutBot con la sesión iniciada.  
Escenario exitoso principal:  
    1. El usuario selecciona la opción "buscar/listar ligas".  
    2. El sistema busca y muestra la lista de todas las ligas (públicas y privadas).  
    3. El usuario selecciona una liga de la lista.  
Escenarios alternativos:  
    2.a No hay ligas registradas.  
        - El sistema devuelve la lista vacía y un mensaje que dice "no hay ligas registradas".  

### Caso de uso 22: Unirse a liga publica
Actor principal: Usuario.  
Precondición: Tener una plantilla.  
Escenario Exitoso:  
	1. El usuario entra en el buscador de Ligas.  
	2. El sistema le muestra al usuario una lista de Ligas a las que se puede unir.  
	3. El usuario selecciona una Liga.  
	4. El sistema le muestra al usuario los detalles de esa Liga (Clubs que participan, duración de los partidos, si es privada o no).  
	5. El usuario le da a unirse a Liga.  
	6. El sistema registra al usuario en la Liga.  
Escenarios excepcionales:  
	6. a) La Liga ya está llena.  
		- El sistema anula la operación de unirse, le manda un aviso al usuario y vuelve a los detalles de la Liga.  

### Caso de uso 23: Unirse a liga privada
Actor principal: Usuario.  
Precondición: Tener una plantilla.  
Escenario Exitoso:  
	1. El usuario entra en el buscador de Ligas.  
	2. El sistema le muestra al usuario una lista de Ligas a las que se puede unir.  
	3. El usuario selecciona una Liga.  
	4. El sistema le muestra al usuario los detalles de esa Liga (Clubs que participan, duración de los partidos, si es privada o no).  
	5. El usuario le da a unirse a Liga.  
	6. El sistema le pide al usuario que ingrese una contraseña.  
	7. El usuario ingresa la contraseña.  
	8. El sistema verifica la contraseña y registra al usuario en la Liga.  
Escenarios excepcionales:  
	6. a) La Liga ya está llena.  
		- El sistema anula la operación de unirse, le manda un aviso al usuario y vuelve a los detalles de la Liga.  
	8. a) La contraseña ingresada es incorrecta.  
		- El sistema le avisa al usuario que ingreso una contraseña incorrecta y no lo agrega a la Liga.  

### Caso de uso 24: Abandonar liga.
Actor primario: Usuario.  
Precondición: El usuario tiene que estar en una liga.  
Escenario exitoso principal:  
El usuario va a la sección de ligas y busca la liga.  
El sistema le muestra el perfil de la liga y las opciones.  
El usuario selecciona la opción de abandonar.  
El sistema retira el club del usuario de la liga.  
Escenarios excepcionales:  
El id/nombre de la liga no existe o está mal ingresado.  
El sistema muestra una lista vacía con el mensaje: “sin resultados encontrados”.  
La liga ya está iniciada.  
El sistema notifica al jugador que la liga ya empezó y no se puede abandonar.  


### Caso de uso 25: Cancelar liga.  
Actor primario: Usuario creador de liga.  
Precondición: Liga aún no iniciada.  
Escenario exitoso principal:  
El usuario creador accede a la liga.  
El usuario selecciona la opción “cancelar liga”  
El sistema cancela la liga, notifica a los clubes que se habían unido.  
Escenarios excepcionales:  
Ninguno.  


### Caso de uso 26: Ver ranking global.  
Actor primario: Usuario.  
Precondición: El usuario debe tener una cuenta y la sesión iniciada.  
Escenario exitoso principal:  
El usuario selecciona la opción “ver ranking global”  
El sistema busca la tabla de puntajes.  
El sistema muestra al usuario el resultado de la tabla de ranking de mayor a menor.  
Escenarios excepcionales:  
     3.a   No hay resultados registrados de ninguna liga.  
El sistema devuelve la tabla vacía y un mensaje que dice “no hay datos registrados”.  


## Gestión durante partidos:

### Caso de uso 27: Crear partido amistoso  
Actor primario: Usuario  
Precondición: Usuario válido y con una plantilla.  
Escenario Exitoso:  
	1. El usuario abre el menú con la lista de partidos amistosos.  
	2. El sistema le muestra la lista de partidos amistosos y la opción de crear uno al usuario.  
	3. El usuario hace click en la opción de “crear partido amistoso”.  
	4. El sistema le muestra al usuario el “formulario” (menú) con los datos que tiene que rellenar.  
	5. El usuario ingresa los datos para el partido amistoso (Duration, su plantilla y contraseña opcional).  
	6. El sistema verifica los datos y crea el partido amistoso.  
Escenarios Excepcionales:  
Ninguno.  


### Caso de uso 28: Unirse a partido amistoso.  
Actor primario: Usuario.  
Precondición: El usuario debe tener una cuenta y la sesión iniciada, y pertenecer a un club con al menos 6 jugadores disponibles.  
Escenario exitoso principal:  
    1. El Usuario selecciona la opción "unirse a partido amistoso".  
    2. El Sistema busca los partidos amistosos con estado "pendiente" y que aún no tengan dos equipos asignados, y muestra la lista.  
    3. El Usuario selecciona un partido amistoso de la lista.  
    4. El Sistema une al usuario al partido amistoso seleccionado.  
Escenarios excepcionales:  
    2.a No hay partidos amistosos con estado pendiente y cupo disponible  
     El sistema devuelve una lista vacía y un mensaje que dice "no hay partidos disponibles".  
    4.a El partido seleccionado ya no está disponible (otro club se unió primero o cambió de estado)  
     El sistema informa al usuario que el partido ya no está disponible y le muestra la lista actualizada.  


### Caso de uso 29: Ver partido en vivo
Actor principal: Usuario  
Precondición:  
    - Debe de haber un partido entre otros usuarios en curso que el actor principal pueda espectar   
Escenario principal:  
    1. El usuario selecciona el partido en curso que quiere visualizar.  
    2. El sistema conecta al usuario con el partido y lo muestra en tiempo real  
    3. El sistema carga el panel de los equipos únicamente mostrando los jugadores y las estadísticas.

### Caso de uso 30: Realizar cambio de jugador  
Actor Primario: Usuario  
Precondición:  
    - El usuario dispone de un cambio antes de la siguiente pausa.  
Escenario exitoso principal:  
    1. El Usuario selecciona la opción de realizar sustitución.  
    2. El usuario selecciona 2 jugadores uno titular y otro suplente.  
    3. El usuario confirma la sustitución.  
    4. El sistema registra la sustitución e informa al usuario.  
    5. El sistema realiza la sustitución cuando empiece una pausa o esté en una.  
Escenario excepcional:  
	2a. El usuario selecciona 2 titulares o 2 suplentes.  
	 *. El sistema informa al usuario que debe seleccionar exactamente un titular
	    y un suplente.  
Escenario alternativo:  
	3a. El usuario cancela la sustitución en curso.  
	 *. El sistema informa al usuario que se canceló la sustitución.  

### Caso de uso 31: Cancelar/modificar sustitución planificada
Actor principal: Usuario  
Precondición:  
    -El usuario debe estar en un partido en curso  
    -Debe de haber una sustitución ya planificada  
Escenario principal:  
    1. El usuario accede al panel de gestión de jugadores y comportamientos.  
    2. El usuario selecciona los cambios que ya estaban planificados  
    3. El usuario realiza una modificación en lo seleccionado.  
    4. El sistema valida que el nuevo suplente esté disponible y que no se está excediendo de la cantidad de cambios disponibles.  
    5. El sistema actualiza la planificación y queda en espera de la pausa.  
Escenarios excepcionales:  
    3a. En vez de realizar una modificación, el usuario decide cancelar los cambios planificados  
        -El sistema elimina la planificación  
        -El sistema devuelve los cupos de cambio si es pertinente  

