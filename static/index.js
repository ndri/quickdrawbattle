window.onload = () => {
    document.getElementById("drawing1").onclick = vote;
    document.getElementById("drawing2").onclick = vote;
    draw("drawing1", []);
    draw("drawing2", []);

    newBattle();
};

function updateCategory(category) {
    const categoryElement = document.getElementById("category");
    categoryElement.innerHTML = category;
}

function vote() {
    if (timeout_count > 0) {
        return;
    }

    const request = new XMLHttpRequest();
    const uuid = this.parentNode.getAttribute("data-battle");
    const category = document.getElementById("selectcategory").value;

    const loadingicon = document.getElementById("loadingicon");

    request.onreadystatechange = () => {
        if (request.readyState === 4) {
            if (request.status === 200) {
                const data = JSON.parse(request.responseText);
                if (data.success) {
                    loadingicon.classList.add("hidden");
                    drawBattle(data);
                } else {
                    alert(data.reason);
                }
            }
        }
    };

    let choice;
    if (this.id === "drawing1") {
        choice = "1";
    } else if (this.id === "drawing2") {
        choice = "2";
    } else {
        choice = "0";
    }

    let queryData = {
        "battle": uuid,
        "choice": choice,
        "category": category
    };

    loadingicon.classList.remove("hidden");
    request.open("GET", "api/vote?" + encodeQueryData(queryData));
    request.send();
}

function newBattle() {
    const category = document.getElementById("selectcategory").value;
    const request = new XMLHttpRequest();
    const loadingicon = document.getElementById("loadingicon");

    request.onreadystatechange = () => {
        if (request.readyState === 4) {
            if (request.status === 200) {
                const data = JSON.parse(request.responseText);
                loadingicon.classList.add("hidden");
                drawBattle(data);
            }
        }
    };

    let queryData = {
        "category": category
    };

    loadingicon.classList.remove("hidden");
    request.open("GET", "api/new_battle?" + encodeQueryData(queryData));
    request.send();
}

function drawBattle(battle) {
    const battleElement = document.getElementById("battle");
    draw("drawing1", battle.strokes1, 1);
    draw("drawing2", battle.strokes2, 1);
    battleElement.setAttribute("data-battle", battle.id);
    updateCategory(battle.category);
}
