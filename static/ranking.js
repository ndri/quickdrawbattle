window.onload = () => {
    const selectcategory = document.getElementById("selectcategory");
    const pagenumber = document.getElementById("pagenumber");

    function updateTable() {
        getRanking("rankingtable", selectcategory.value, pagenumber.value);
    }

    updateTable();
    pagenumber.onchange = updateTable;
    selectcategory.onchange = () => {
        pagenumber.value = 1;
        updateTable();
    };
};

// https://stackoverflow.com/a/111545/12123296
function encodeQueryData(data) {
   const ret = [];
   for (let d in data) {
       ret.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
   }
   return ret.join("&");
}

function getRanking(tableID, category = "any", page = 1) {
    if (page < 1) page = 1;

    const request = new XMLHttpRequest();
    const limit = 25;
    let offset = (page - 1) * limit;

    const loadingicon = document.getElementById("loadingicon");

    request.onreadystatechange = () => {
        if (request.readyState === 4) {
            if (request.status === 200) {
                const data = JSON.parse(request.responseText);
                let maxPage = Math.ceil(data["count"] / limit);
                document.getElementById("pagenumber").max = maxPage;
                document.getElementById("maxpage").innerHTML = maxPage;
                fillTable(tableID, data["drawings"], offset);
                loadingicon.classList.add("hidden");
            }
        }
    };

    let queryData = {
        "category": category,
        "offset": offset,
        "limit": limit,
        "strokes": true,
        "votemin": 0
    };

    loadingicon.classList.remove("hidden");
    request.open("GET", "/api/get_ranking?" + encodeQueryData(queryData));
    request.send();
}

function fillTable(tableID, drawings, offset) {
    const table = document.getElementById(tableID);
    const tbody = table.getElementsByTagName("tbody")[0];
    tbody.innerHTML = "";

    for (let i = 0; i < drawings.length; i++) {
        let drawing = drawings[i];
        let tr = tbody.insertRow();

        tr.insertCell().innerText = offset + i + 1;

        let canvasCell = tr.insertCell();
        let canvas = document.createElement("canvas");
        canvas.id = "drawing" + drawing.key_id;
        canvasCell.appendChild(canvas);
        draw(canvas.id, drawing.strokes, 0.5);

        tr.insertCell().innerText = drawing.category;
        tr.insertCell().innerText = drawing.countrycode;
        tr.insertCell().innerText = drawing.wins;
        tr.insertCell().innerText = drawing.losses;
        tr.insertCell().innerText = (drawing.score).toFixed(4);
    }
}