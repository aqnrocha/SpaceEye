function select_item(id, text) {
    if (id === "selected-item-view") {
        document.getElementById(id).innerText = text;
        alternar_conteudo(text);
        
    } else if (id === "selected-item-image") {
        document.getElementById(id).innerText = text;
        alternar_ndvi(text);

    } else {
        document.getElementById(id).value = text;
        document.getElementById(id).innerText = text;
        
        if (id === "selected-item-uf") {
            load_cities_select(text);
        } else if (id === "selected-item-property") {
            alternar_propriedade(text);
        }
    }
}

function hide(id) {
    document.getElementById(id).style.display = "none";
}

function show(id) {
    document.getElementById(id).style.display = "flex";
}

function show_or_hide_dropdown(id) {

    const dropdown_uf = document.getElementById("dropdown");
    const dropdown_city = document.getElementById("dropdown-city");
    
    if (id === "dropdown") {

        if (dropdown_uf.style.display === "none") {
            show("dropdown");
            hide("dropdown-city");
        } else {
            hide("dropdown");
        }

    } else if (id === "dropdown-city") {

        if (dropdown_city.style.display === "none") {
            show("dropdown-city");
            hide("dropdown");
        } else {
            hide("dropdown-city");
        }    

    } else if (id === "dropdown-property") {

        const dropdown_view = document.getElementById(id);

        if (dropdown_view.style.display === "none") {
            show(id);
            hide("dropdown-image");
        } else {
            hide(id);
        }

    } else if (id === "dropdown-image") {
        const dropdown_view = document.getElementById(id);

        if (dropdown_view.style.display === "none") {
            show(id);
            hide("dropdown-property");
        } else {
            hide(id);
        }
    } else {
        const dropdown_view = document.getElementById(id);

        if (dropdown_view.style.display === "none") {
            show(id);
        } else {
            hide(id);
        }        
    }
}

async function request(endpoint) {
    const api = endpoint;
    const response = await fetch(api);
    if (!response.ok) {
        throw new Error('Erro ao fazer a requisição: ' + response.statusText);
    }
    const data = await response.json();
    return data;
}

function loadOptions(id, id_name, texto) {
    const select = document.getElementById(id);
    const novaOpcao = document.createElement("div");
    novaOpcao.innerText = texto;

    if (id === "dropdown-city") {
        novaOpcao.className = "dropdown-item-city";
    } else {
        novaOpcao.className = "dropdown-item";
    }

    let function_name = `select_item("${id_name}", "${texto}")`;
    novaOpcao.setAttribute("onclick", function_name);
    select.appendChild(novaOpcao);
}    

async function load_uf_select() {
    const api_uf = "http://localhost:5001/api/IBGE/uf";
    const ufs = await request(api_uf);

    ufs.sort().forEach(uf => {
        loadOptions("dropdown", "selected-item-uf", uf);
    });
}

async function load_cities_select(uf) {
    const api_cidades = `http://localhost:5001/api/IBGE/cidades/${uf}`;
    const cidades = await request(api_cidades);
    
    const select = document.getElementById("dropdown-city");
    select.innerHTML = "";

    cidades.sort((a, b) => a.localeCompare(b)).forEach(cidade => {
        loadOptions("dropdown-city", "selected-item-city", cidade);
    });
}


function filter(id_input, options_class, id_dropdown) {
    const input = document.getElementById(id_input);
    input.addEventListener("input", (event) => {
        let lista_elementos = document.getElementsByClassName(options_class);
        for (let i = 0; i < lista_elementos.length; i++) {
            let texto = lista_elementos[i].innerText;
            const contem_substring = texto.includes(input.value);
            
            if (contem_substring) {
                lista_elementos[i].style.display = "flex";
                document.getElementById(id_dropdown).style.display = "flex";
            } else {
                lista_elementos[i].style.display = "none";
            }
        }
    });
}

async function find() {
    const map = document.getElementById("map");

    let estado = document.getElementById("selected-item-uf").value;
    let cidade = document.getElementById("selected-item-city").value;

    let response = await fetch(`http://localhost:5001/api/map/${estado}/${cidade}`);
    let data = await response.json();
    map.innerHTML = "";
    map.innerHTML = data["HTML"];
}

async function goTo(route) {
    window.location.href = "/" + route;
}

(async () => {
    try {
        await load_uf_select();
        filter("selected-item-uf", "dropdown-item", "dropdown");
        filter("selected-item-city", "dropdown-item-city", "dropdown-city");      
    } catch (error) {
        console.error('Erro ao selecionar propriedade:', error);
    }
})();   