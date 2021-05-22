let drawing1, drawing2;

window.onload = () => {
    drawing1 = document.getElementById("drawing1")
    drawing1.onclick = vote;
    drawing2 = document.getElementById("drawing2")
    drawing2.onclick = vote;
    draw("drawing1", []);
    draw("drawing2", []);

    document.getElementById("skipbutton").onclick = newBattle;

    newBattle();
};

function updateCategory(category) {
    const categoryElement = document.getElementById("category");
    categoryElement.innerHTML = category;
}

function vote() {
    if (!drawing1.classList.contains("ready") || !drawing2.classList.contains("ready")) {
        return;
    }

    const uuid = this.parentNode.getAttribute("data-battle");
    const category = document.getElementById("selectcategory").value;
    const loadingicon = document.getElementById("loadingicon");

    let choice;
    if (this.id === "drawing1") {
        choice = "1";
    } else if (this.id === "drawing2") {
        choice = "2";
    } else {
        choice = "0";
    }

    drawing1.classList.remove("ready");
    drawing2.classList.remove("ready");
    loadingicon.classList.remove("hidden");

    fetch("api/vote", {
        method: "POST",
        headers: json_headers,
        body: JSON.stringify({
            battle: uuid,
            choice: choice,
            category: category
        })
    }).then(
        response => response.json()
    ).then(data => {
        if (data.success) {
            loadingicon.classList.add("hidden");
            drawBattle(data);
        } else {
            alert(data.reason);
        }
    })
}

async function newBattle() {
    if (!drawing1.classList.contains("ready") || !drawing2.classList.contains("ready")) {
        return;
    }

    const category = document.getElementById("selectcategory").value;
    const loadingicon = document.getElementById("loadingicon");
    drawing1.classList.remove("ready");
    drawing2.classList.remove("ready");

    loadingicon.classList.remove("hidden");
    fetch("api/new_battle", {
        method: "POST",
        headers: json_headers,
        body: JSON.stringify({
            category: category
        })
    }).then(
        response => response.json()
    ).then(data => {
        loadingicon.classList.add("hidden");
        drawBattle(data);
    });
}

function drawBattle(battle) {
    const battleElement = document.getElementById("battle");

    // replace drawings so mobile hover goes away
    const drawing1_clone = drawing1.cloneNode(true);
    const drawing2_clone = drawing2.cloneNode(true);
    drawing1.replaceWith(drawing1_clone);
    drawing2.replaceWith(drawing2_clone);
    drawing1 = drawing1_clone;
    drawing2 = drawing2_clone;
    drawing1.onclick = vote;
    drawing2.onclick = vote;

    draw("drawing1", battle.strokes1, 1);
    draw("drawing2", battle.strokes2, 1);
    battleElement.setAttribute("data-battle", battle.id);
    updateCategory(battle.category);
}
