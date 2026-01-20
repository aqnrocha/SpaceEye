async function loading_page(show) {
    const content = document.getElementById("loading-page-container");

    if (show) {
        console.log("Mostrando loading page");
        content.style.display = "flex";
    } else {
        console.log("Escondendo loading page");
        content.style.display = "none";
    }
}    

function close_modal(id) {
    document.getElementById(id).style.display = "none";
}

function open_modal(id) {
    document.getElementById(id).style.display = "flex";
}

async function sendPolygon() {
    parent.document.getElementById("modal-save-polygon").style.display = "none";
    await loading_page(true);

    let data = document.getElementById("coordinates-textarea").value;
    let options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    };
    
    try {
        let response = await fetch("http://localhost:5001/api/images", options)
        let imagens = await response.json();
        document.getElementById("modal-view-images").style.display = "flex";

        const container = document.getElementById("image-list");
        const divsToRemove = container.querySelectorAll('div.image-container');
        divsToRemove.forEach(div => div.remove());
        
        if (imagens.length < 1) {
            document.getElementById("no-images").style.display = "flex";
    
        } else {

            document.getElementById("no-images").style.display = "none";
            
            for (let i = 0; i < imagens.length; i++) {
    
                let newdiv = document.createElement("div");
                newdiv.className = "image-container";
                newdiv.setAttribute("onclick", `processImage('${imagens[i]["id"]}')`)
    
                let title = document.createElement("p");
                title.className = "image-title";
    
                let cloud = document.createElement("p");
                let time = document.createElement("p");
                let thumb = document.createElement("img");
                let date = new Date(imagens[i]["data"])
    
                title.innerText = imagens[i]["id"];
                cloud.innerText = `Cloud Cover: ${imagens[i]["cloud_cover"]}`;
                time.innerText = `Data: ${date}`;
    
                thumb.setAttribute("src", imagens[i]["thumbnail"]);
    
                newdiv.appendChild(title);
                newdiv.appendChild(cloud);
                newdiv.appendChild(time);
                newdiv.appendChild(thumb);
    
                container.appendChild(newdiv);
            }        
        }
    } catch(error) {
        document.getElementById("no-images").style.display = "flex";
    }

    await loading_page(false);
}

document.addEventListener("DOMContentLoaded", function() {

    async function mapGenerator() {
        const map = document.getElementById("map");
        
        if (map.innerHTML.trim() === '') {
            let response = await fetch("http://localhost:5001/api/map");
            let data = await response.json();
            console.log(data);
            map.innerHTML = data["HTML"];
        }
    }

    window.addEventListener("message", function(event) {
        const target = document.getElementById("coordinates-textarea");
        let data = document.getElementById("coordinates").value;

        target.value = JSON.stringify({
            "Coordenadas": JSON.parse(data)
        }, null, 4);
    });

    function handleInputChange(event) {
        const target = document.getElementById("coordinates-textarea");
        let data = document.getElementById("coordinates").value;

        target.value = JSON.stringify({
            "Coordenadas": JSON.parse(data)
        }, null, 4);
    }

    (async () => {
        await mapGenerator();
    })();
});

async function processImage(imageId) {
    await loading_page(true);
    document.getElementById("modal-view-images").style.display = "none";

    let data = document.getElementById("coordinates").value;
    let body = {
        'coordinates': data,
        'imageId': imageId
    };
    console.log(body);

    let options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    };

    let response = await fetch(`http://localhost:5001/api/processImage`, options);
    console.log(response);
    if (response.status === 200) {
        await viewRaster(imageId);
    }
}

async function viewRaster(imageId) {
    let data = document.getElementById("coordinates").value;

    let options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            coordinates: data,
            imageId: imageId
        })
    };
    
    let response = await fetch(`http://localhost:5001/api/raster_view`, options);
    let mapHtml = await response.json();
    console.log(mapHtml);
    
    const mapElement = document.getElementById("map2");
    mapElement.innerHTML = "";
    mapElement.innerHTML = mapHtml["html"];
    
    await loading_page(false);
    document.getElementById("modal-analysis-container").style.display = "flex";
}

async function close_modal(id) {
    document.getElementById(id).style.display = "none";
}