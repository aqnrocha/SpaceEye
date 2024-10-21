async function load_imageCards(data) {

    const container = document.getElementById("image-list");
    for (let i = 0; i < data.length; i++) {

        let newdiv = document.createElement("div");
        newdiv.className = "image-container";

        let title = document.createElement("p");
        title.className = "image-title";

        let cloud = document.createElement("p");
        let time = document.createElement("p");
        let thumb = document.createElement("img");

        title.innerText = data[i]["id"];
        cloud.innerText = `Cloud Cover: ${data[i]["cloud_cover"]}`;
        time.innerText = `Data: ${data[i]["data/hora"]}`;

        thumb.setAttribute("src", data[i]["thumbnail"]);

        newdiv.appendChild(title);
        newdiv.appendChild(cloud);
        newdiv.appendChild(time);
        newdiv.appendChild(thumb);

        container.appendChild(newdiv);
    }
}