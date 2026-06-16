// Lista de países (América + Caribe + Europa). Venezuela primero (por defecto).
const PAISES = [
  "Venezuela",
  // América
  "Argentina", "Belice", "Bolivia", "Brasil", "Canadá", "Chile", "Colombia",
  "Costa Rica", "Ecuador", "El Salvador", "Estados Unidos", "Guatemala",
  "Guyana", "Honduras", "México", "Nicaragua", "Panamá", "Paraguay", "Perú",
  "Surinam", "Uruguay",
  // Caribe (islas)
  "Antigua y Barbuda", "Aruba", "Bahamas", "Barbados", "Cuba", "Curazao",
  "Dominica", "Granada", "Haití", "Islas Caimán", "Islas Vírgenes (EE.UU.)",
  "Jamaica", "Puerto Rico", "República Dominicana", "San Cristóbal y Nieves",
  "San Vicente y las Granadinas", "Santa Lucía", "Trinidad y Tobago",
  // Europa
  "Albania", "Alemania", "Andorra", "Austria", "Bélgica", "Bielorrusia",
  "Bosnia y Herzegovina", "Bulgaria", "Chipre", "Croacia", "Dinamarca",
  "Eslovaquia", "Eslovenia", "España", "Estonia", "Finlandia", "Francia",
  "Grecia", "Hungría", "Irlanda", "Islandia", "Italia", "Letonia", "Lituania",
  "Luxemburgo", "Malta", "Moldavia", "Mónaco", "Montenegro", "Noruega",
  "Países Bajos", "Polonia", "Portugal", "Reino Unido", "República Checa",
  "Rumania", "Rusia", "Serbia", "Suecia", "Suiza", "Ucrania"
];

// Datos detallados (País → Estado → Municipios). Ampliable país por país.
// Donde no haya datos, los campos Estado/Municipio se escriben libremente.
const UBICACIONES = {
  "Venezuela": {
    "Distrito Capital": ["Libertador"],
    "Amazonas": ["Alto Orinoco", "Atabapo", "Atures", "Autana", "Manapiare", "Maroa", "Río Negro"],
    "Anzoátegui": ["Anaco", "Aragua", "Manuel Ezequiel Bruzual", "Diego Bautista Urbaneja", "Fernando de Peñalver", "Francisco del Carmen Carvajal", "Francisco de Miranda", "Guanta", "Independencia", "José Gregorio Monagas", "Juan Antonio Sotillo", "Juan Manuel Cajigal", "Libertad", "Pedro María Freites", "Píritu", "San José de Guanipa", "San Juan de Capistrano", "Santa Ana", "Simón Bolívar", "Simón Rodríguez", "Sir Arthur McGregor"],
    "Apure": ["Achaguas", "Biruaca", "Muñoz", "Páez", "Pedro Camejo", "Rómulo Gallegos", "San Fernando"],
    "Aragua": ["Bolívar", "Camatagua", "Francisco Linares Alcántara", "Girardot", "José Ángel Lamas", "José Félix Ribas", "José Rafael Revenga", "Libertador", "Mario Briceño Iragorry", "Ocumare de la Costa de Oro", "San Casimiro", "San Sebastián", "Santiago Mariño", "Santos Michelena", "Sucre", "Tovar", "Urdaneta", "Zamora"],
    "Barinas": ["Alberto Arvelo Torrealba", "Andrés Eloy Blanco", "Antonio José de Sucre", "Arismendi", "Barinas", "Bolívar", "Cruz Paredes", "Ezequiel Zamora", "Obispos", "Pedraza", "Rojas", "Sosa"],
    "Bolívar": ["Caroní", "Cedeño", "El Callao", "Gran Sabana", "Heres", "Padre Pedro Chien", "Piar", "Angostura (Raúl Leoni)", "Roscio", "Sifontes", "Sucre"],
    "Carabobo": ["Bejuma", "Carlos Arvelo", "Diego Ibarra", "Guacara", "Juan José Mora", "Libertador", "Los Guayos", "Miranda", "Montalbán", "Naguanagua", "Puerto Cabello", "San Diego", "San Joaquín", "Valencia"],
    "Cojedes": ["Anzoátegui", "Tinaco", "Girardot", "Lima Blanco", "Pao de San Juan Bautista", "Ricaurte", "Rómulo Gallegos", "San Carlos", "Tinaquillo"],
    "Delta Amacuro": ["Antonio Díaz", "Casacoima", "Pedernales", "Tucupita"],
    "Falcón": ["Acosta", "Bolívar", "Buchivacoa", "Cacique Manaure", "Carirubana", "Colina", "Dabajuro", "Democracia", "Falcón", "Federación", "Jacura", "Los Taques", "Mauroa", "Miranda", "Monseñor Iturriza", "Palmasola", "Petit", "Píritu", "San Francisco", "Silva", "Sucre", "Tocópero", "Unión", "Urumaco", "Zamora"],
    "Guárico": ["Camaguán", "Chaguaramas", "El Socorro", "Francisco de Miranda", "José Félix Ribas", "José Tadeo Monagas", "Juan Germán Roscio", "Julián Mellado", "Las Mercedes", "Leonardo Infante", "Ortiz", "Pedro Zaraza", "San Gerónimo de Guayabal", "San José de Guaribe", "Santa María de Ipire"],
    "Lara": ["Andrés Eloy Blanco", "Crespo", "Iribarren", "Jiménez", "Morán", "Palavecino", "Simón Planas", "Torres", "Urdaneta"],
    "Mérida": ["Alberto Adriani", "Andrés Bello", "Antonio Pinto Salinas", "Aricagua", "Arzobispo Chacón", "Campo Elías", "Caracciolo Parra Olmedo", "Cardenal Quintero", "Guaraque", "Julio César Salas", "Justo Briceño", "Libertador", "Miranda", "Obispo Ramos de Lora", "Padre Noguera", "Pueblo Llano", "Rangel", "Rivas Dávila", "Santos Marquina", "Sucre", "Tovar", "Tulio Febres Cordero", "Zea"],
    "Miranda": ["Acevedo", "Andrés Bello", "Baruta", "Brión", "Buroz", "Carrizal", "Chacao", "Cristóbal Rojas", "El Hatillo", "Guaicaipuro", "Independencia", "Lander", "Los Salias", "Páez", "Paz Castillo", "Pedro Gual", "Plaza", "Simón Bolívar", "Sucre", "Urdaneta", "Zamora"],
    "Monagas": ["Acosta", "Aguasay", "Bolívar", "Caripe", "Cedeño", "Ezequiel Zamora", "Libertador", "Maturín", "Piar", "Punceres", "Santa Bárbara", "Sotillo", "Uracoa"],
    "Nueva Esparta": ["Antolín del Campo", "Arismendi", "Díaz", "García", "Gómez", "Maneiro", "Marcano", "Mariño", "Península de Macanao", "Tubores", "Villalba"],
    "Portuguesa": ["Agua Blanca", "Araure", "Esteller", "Guanare", "Guanarito", "Monseñor José Vicente de Unda", "Ospino", "Páez", "Papelón", "San Genaro de Boconoíto", "San Rafael de Onoto", "Santa Rosalía", "Sucre", "Turén"],
    "Sucre": ["Andrés Eloy Blanco", "Andrés Mata", "Arismendi", "Benítez", "Bermúdez", "Bolívar", "Cajigal", "Cruz Salmerón Acosta", "Libertador", "Mariño", "Mejía", "Montes", "Ribero", "Sucre", "Valdez"],
    "Táchira": ["Andrés Bello", "Antonio Rómulo Costa", "Ayacucho", "Bolívar", "Cárdenas", "Córdoba", "Fernández Feo", "Francisco de Miranda", "García de Hevia", "Guásimos", "Independencia", "Jáuregui", "José María Vargas", "Junín", "Libertad", "Libertador", "Lobatera", "Michelena", "Panamericano", "Pedro María Ureña", "Rafael Urdaneta", "Samuel Darío Maldonado", "San Cristóbal", "San Judas Tadeo", "Seboruco", "Simón Rodríguez", "Sucre", "Torbes", "Uribante"],
    "Trujillo": ["Andrés Bello", "Boconó", "Bolívar", "Candelaria", "Carache", "Carvajal", "Escuque", "Juan Vicente Campo Elías", "La Ceiba", "Miranda", "Monte Carmelo", "Motatán", "Pampán", "Pampanito", "Rangel", "Sucre", "Trujillo", "Urdaneta", "Valera"],
    "La Guaira": ["Vargas"],
    "Yaracuy": ["Arístides Bastidas", "Bolívar", "Bruzual", "Cocorote", "Independencia", "José Antonio Páez", "La Trinidad", "Manuel Monge", "Nirgua", "Peña", "San Felipe", "Sucre", "Urachiche", "Veroes"],
    "Zulia": ["Almirante Padilla", "Baralt", "Cabimas", "Catatumbo", "Colón", "Francisco Javier Pulgar", "Jesús Enrique Lossada", "Jesús María Semprún", "La Cañada de Urdaneta", "Lagunillas", "Machiques de Perijá", "Mara", "Maracaibo", "Miranda", "Páez", "Rosario de Perijá", "San Francisco", "Santa Rita", "Simón Bolívar", "Sucre", "Valmore Rodríguez"]
  }
};

function initUbicaciones(paisId, estadoId, municipioId, listaEstadosId, listaMunicipiosId, def) {
  const pais = document.getElementById(paisId);
  const estado = document.getElementById(estadoId);
  const municipio = document.getElementById(municipioId);
  const listaEstados = document.getElementById(listaEstadosId);
  const listaMunicipios = document.getElementById(listaMunicipiosId);
  def = def || {};

  function opciones(datalist, items) {
    datalist.innerHTML = "";
    items.forEach(function (it) {
      const o = document.createElement("option");
      o.value = it;
      datalist.appendChild(o);
    });
  }

  // Llenar el menú de países
  pais.innerHTML = '<option value="">Seleccionar país</option>';
  PAISES.forEach(function (p) {
    const o = document.createElement("option");
    o.value = p;
    o.textContent = p;
    if (p === def.pais) o.selected = true;
    pais.appendChild(o);
  });

  function refrescarEstados() {
    const data = UBICACIONES[pais.value];
    opciones(listaEstados, data ? Object.keys(data) : []);
    refrescarMunicipios();
  }

  function refrescarMunicipios() {
    const data = UBICACIONES[pais.value];
    const muni = data && data[estado.value] ? data[estado.value] : [];
    opciones(listaMunicipios, muni);
  }

  pais.addEventListener("change", function () {
    estado.value = "";
    municipio.value = "";
    refrescarEstados();
  });
  estado.addEventListener("change", function () {
    municipio.value = "";
    refrescarMunicipios();
  });
  estado.addEventListener("input", refrescarMunicipios);

  // Valores por defecto
  refrescarEstados();
  if (def.estado) estado.value = def.estado;
  refrescarMunicipios();
  if (def.municipio) municipio.value = def.municipio;
}
